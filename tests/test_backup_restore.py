"""Exercise real backup/restore bodies with isolated SQLite and asset folders."""
import ast
from contextlib import closing, contextmanager
import datetime
import io
import json
import logging
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]


class BackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='edrefcard-backup-test-')
        self.root=Path(self.temp.name)
        self.configs=self.root/'source';self.configs.mkdir()
        self.maintenance=[]
        self.reconnected=[]
        @contextmanager
        def get_db():
            with closing(sqlite3.connect(self.configs/'edrefcard.db')) as conn:
                yield conn
                conn.commit()
        fake_database=types.SimpleNamespace(get_db=get_db,init_db=self.reconnected.append)
        package=types.ModuleType('scripts');package.database=fake_database
        self.modules=patch.dict(sys.modules,{'scripts':package})
        self.modules.start();self.addCleanup(self.modules.stop)
        self.env={'__file__':str(self.root/'code/www/admin/backup.py'),
            'Config':types.SimpleNamespace(configsPath=lambda:self.configs),
            'Path':Path,'os':os,'json':json,'shutil':shutil,'tarfile':tarfile,
            'tempfile':tempfile,'datetime':datetime,'sqlite3':sqlite3,'closing':closing,'uuid4':uuid4,
            '_CONTROLLER_IMAGE_SUFFIXES':frozenset({'.jpg','.jpeg','.png','.webp'}),
            'logger':logging.getLogger('backup-test'),
            'log_backup_history':lambda **kwargs:None,
            'set_maintenance_mode':lambda enabled,*args:self.maintenance.append(enabled)}
        tree=ast.parse((ROOT/'www/admin/backup.py').read_text(encoding='utf-8'))
        nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('BackupManager','RestoreManager')]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-backup-restore','exec'),self.env)
        self.env['RestoreManager'].reload_gunicorn=lambda instance:False
        with closing(sqlite3.connect(self.configs/'edrefcard.db')) as conn:
            conn.executescript('CREATE TABLE backup_settings(id INTEGER PRIMARY KEY,last_backup_at TEXT,last_backup_status TEXT);'
                'INSERT INTO backup_settings(id) VALUES (1);'
                'CREATE TABLE controller_mappings(id INTEGER PRIMARY KEY,mapping_json TEXT);'
                'INSERT INTO controller_mappings VALUES(1,\'{"image":"controller-one"}\');')
        (self.configs/'controllers').mkdir()
        (self.configs/'controllers/controller-one.jpg').write_bytes(b'controller-source-image')
        (self.configs/'controllers/other.webp').write_bytes(b'another-source-image')
        (self.configs/'controllers/ignored.txt').write_text('not an image')
        (self.configs/'ab').mkdir()
        (self.configs/'ab/abcdef.binds').write_text('<Root/>')
        (self.configs/'ab/abcdef-controller.jpg').write_bytes(b'generated card')
        (self.configs/'ab/abcdef-A4.pdf').write_bytes(b'generated PDF')

    def tearDown(self):
        self.temp.cleanup()

    def manager(self):
        return self.env['BackupManager']()

    def restore(self,archive,**kwargs):
        return self.env['RestoreManager']().restore_from_archive(archive,**kwargs)

    def destination(self):
        self.configs=self.root/'restored';self.configs.mkdir()

    def test_round_trip_database_binds_and_source_images(self):
        archive=self.manager().create_backup()
        with tarfile.open(archive) as tar:
            names=set(tar.getnames())
            self.assertIn('controllers/controller-one.jpg',names)
            self.assertIn('controllers/other.webp',names)
            self.assertNotIn('controllers/ignored.txt',names)
            self.assertFalse(any(n.endswith('.pdf') or 'abcdef-controller' in n for n in names))
            metadata=json.load(tar.extractfile('metadata.json'))
            self.assertEqual(metadata['version'],'2.0')
            self.assertTrue(metadata['includes_controller_images'])
        self.destination()
        result=self.restore(archive,create_safety_backup=False)
        self.assertTrue(result['success'],result)
        self.assertEqual(result['controller_images_restored'],2)
        self.assertEqual(result['binds_restored'],1)
        self.assertEqual((self.configs/'controllers/controller-one.jpg').read_bytes(),b'controller-source-image')
        with closing(sqlite3.connect(self.configs/'edrefcard.db')) as restored:
            self.assertEqual(restored.execute('pragma quick_check').fetchone()[0],'ok')
            self.assertEqual(json.loads(restored.execute('select mapping_json from controller_mappings').fetchone()[0])['image'],
                             'controller-one')
        self.assertEqual(self.maintenance,[True,False])
        self.assertEqual(self.reconnected,[str(self.configs/'edrefcard.db')])

    def test_snapshot_contains_committed_wal_data(self):
        with closing(sqlite3.connect(self.configs/'edrefcard.db')) as writer:
            writer.execute('pragma journal_mode=WAL')
            writer.execute('pragma wal_autocheckpoint=0')
            writer.execute('insert into controller_mappings values(2,?)',('{"image":"wal-committed"}',))
            writer.commit()
            archive=self.manager().create_backup()
            with tarfile.open(archive) as tar:
                snapshot=self.root/'snapshot.sqlite'
                snapshot.write_bytes(tar.extractfile('database/edrefcard.db').read())
            with closing(sqlite3.connect(snapshot)) as restored:
                self.assertEqual(restored.execute('select count(*) from controller_mappings').fetchone()[0],2)

    def test_old_archive_without_images_restores_without_deleting_existing_assets(self):
        archive=self.manager().create_backup(include_controller_images=False)
        self.destination()
        (self.configs/'controllers').mkdir()
        existing=self.configs/'controllers/keep.jpg';existing.write_bytes(b'keep')
        result=self.restore(archive,create_safety_backup=False)
        self.assertTrue(result['success'],result)
        self.assertEqual(result['controller_images_restored'],0)
        self.assertEqual(existing.read_bytes(),b'keep')

    def test_binds_only_options_do_not_touch_controller_assets(self):
        archive=self.manager().create_backup(include_db=False)
        with tarfile.open(archive) as tar:
            self.assertFalse(any(n.startswith('controllers/') for n in tar.getnames()))
        self.destination()
        result=self.restore(archive,restore_db=False,create_safety_backup=False)
        self.assertTrue(result['success'],result)
        self.assertEqual(result['binds_restored'],1)
        self.assertFalse((self.configs/'controllers').exists())

    def test_backups_are_unique_even_in_same_second(self):
        manager=self.manager()
        first=manager.create_backup();original=first.read_bytes()
        second=manager.create_backup()
        self.assertNotEqual(first,second)
        self.assertEqual(first.read_bytes(),original)

    def test_safety_backup_failure_aborts_restore(self):
        archive=self.manager().create_backup()
        target=self.configs/'controllers/controller-one.jpg';target.write_bytes(b'keep newer image')
        with patch.object(self.env['BackupManager'],'create_backup',side_effect=OSError('disk unavailable')):
            result=self.restore(archive)
        self.assertFalse(result['success'])
        self.assertIn('Safety backup failed',result['errors'][0])
        self.assertEqual(target.read_bytes(),b'keep newer image')
        self.assertEqual(self.maintenance,[True,False])

    def test_reconnection_failure_is_not_reported_as_success(self):
        archive=self.manager().create_backup()
        self.destination()
        sys.modules['scripts'].database.init_db=lambda path:(_ for _ in ()).throw(RuntimeError('reconnect failed'))
        result=self.restore(archive,create_safety_backup=False)
        self.assertFalse(result['success'])
        self.assertTrue(any('reconnection failed' in error for error in result['errors']))

    def test_archive_image_traversal_and_links_are_rejected(self):
        archive=self.root/'malicious.tar.gz'
        with tarfile.open(archive,'w:gz') as tar:
            for name in ['controllers/../../outside.jpg','controllers/nested/../../../escape.jpg']:
                info=tarfile.TarInfo(name);info.size=4;tar.addfile(info,io.BytesIO(b'evil'))
            for kind in [tarfile.SYMTYPE,tarfile.LNKTYPE]:
                info=tarfile.TarInfo('controllers/link-'+str(kind)+'.jpg');info.type=kind
                info.linkname=str(self.root/'outside.jpg');tar.addfile(info)
        self.destination()
        result=self.restore(archive,restore_db=False,restore_binds=False,
                            restore_controller_images=True,create_safety_backup=False)
        self.assertFalse(result['success'])
        self.assertEqual(result['controller_images_restored'],0)
        self.assertFalse((self.root/'outside.jpg').exists())
        self.assertFalse((self.root/'escape.jpg').exists())


if __name__=='__main__':
    unittest.main()
