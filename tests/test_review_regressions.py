"""Regressions found by the 2026-11 code review.

1. Deleting one config removed the whole two-character prefix directory.
2. Error pages reflected the URL as raw HTML (XSS).
3. Behind the reverse proxy every visitor shared one rate-limit bucket and
   request.is_secure was False (no HSTS, http:// links).
4. Hand-written display-group lists drifted from the parser's names.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from scripts.models import Config

ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / 'www'


class OwnedFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='edrefcard-owned-')
        self.saved = Config._configs_path
        Config.setConfigsPath(self.temp.name)
        self.folder = Path(self.temp.name).resolve() / 'cu'
        self.folder.mkdir()
        for name in ('custom-4-2.binds', 'custom-4-2-t16000m.jpg', 'custom-4-2-A4.pdf',
                     'custom-4-2-abc.binds', 'custom-4-2-abc-t16000m.jpg', 'custom-4-2-abc-A4.pdf',
                     'cuxx.binds', 'cuxx-keyboard.jpg'):
            (self.folder / name).write_text('x')

    def tearDown(self):
        Config._configs_path = self.saved
        self.temp.cleanup()

    def names(self, config_id, other_ids=()):
        return sorted(p.name for p in Config(config_id).ownedFiles(other_ids))

    def test_owner_gets_its_files_and_not_those_of_a_longer_sibling_id(self):
        self.assertEqual(self.names('custom-4-2'),
                         ['custom-4-2-A4.pdf', 'custom-4-2-t16000m.jpg', 'custom-4-2.binds'])

    def test_suffixed_sibling_only_gets_its_own_files(self):
        self.assertEqual(self.names('custom-4-2-abc'),
                         ['custom-4-2-abc-A4.pdf', 'custom-4-2-abc-t16000m.jpg', 'custom-4-2-abc.binds'])

    def test_database_ids_protect_siblings_whose_source_is_missing(self):
        (self.folder / 'custom-4-2-abc.binds').unlink()
        self.assertNotIn('custom-4-2-abc-t16000m.jpg', self.names('custom-4-2', {'custom-4-2-abc'}))

    def test_unknown_config_owns_nothing(self):
        self.assertEqual(self.names('zz-missing'), [])

    def test_only_generated_ids_are_valid_names(self):
        for name in ('custom-4-2-abc', 'abcdef', 'My_Config1'):
            self.assertTrue(Config.isValidName(name), name)
        for name in ('', '..', '../x', 'a/b', 'a*', '<img src=x onerror=alert(1)>', 'a b', None):
            self.assertFalse(Config.isValidName(name), name)


class DisplayGroupTests(unittest.TestCase):
    def test_every_control_group_can_be_displayed(self):
        from scripts.controlsData import controls
        from scripts.parser import ALL_DISPLAY_GROUPS
        used = {control['Group'] for control in controls.values()}
        self.assertEqual(used - set(ALL_DISPLAY_GROUPS), set())

    def test_no_hand_written_group_list_outside_the_parser(self):
        for name in ('api.py', 'admin/__init__.py'):
            source = (WWW / name).read_text(encoding='utf-8')
            self.assertIn('ALL_DISPLAY_GROUPS', source, name)
            self.assertNotIn("'On Foot'", source, name)


# The Flask app is imported in a child process: importing it initializes a
# database and rewires Config for the whole interpreter.
APP_PROBE = textwrap.dedent('''
    import base64, json, os, sys, types
    try:
        import wand.image  # noqa: F401
    except ImportError:
        # ImageMagick absent (developer machine): these checks never render.
        for name in ('wand', 'wand.image', 'wand.drawing', 'wand.color', 'wand.font'):
            module = types.ModuleType(name)
            sys.modules[name] = module
            for attr in ('Image', 'Drawing', 'Color', 'Font'):
                setattr(module, attr, type(attr, (), {'__init__': lambda self, *a, **k: None}))
    www = sys.argv[1]
    sys.path.insert(0, www)
    os.chdir(www)
    import app as appmod
    from scripts import database
    from scripts.models import Config
    from flask import request, url_for
    from flask_limiter.util import get_remote_address

    @appmod.app.route('/__probe')  # routes must exist before the first request
    def probe():
        return json.dumps([get_remote_address(), request.is_secure,
                           url_for('web.show_binds', run_id='x', _external=True)])

    client = appmod.app.test_client()
    out = {}

    payload = '<img src=x onerror=alert(1)>'
    for key, url in (('binds', '/binds/%3Cimg%20src=x%20onerror=alert(1)%3E'),
                     ('device', '/device/%3Cimg%20src=x%20onerror=alert(1)%3E'),
                     ('pdf', '/download/%3Cimg%20src=x%20onerror=alert(1)%3E/pdf'),
                     ('glob', '/download/cu*/pdf'),
                     ('unknown', '/binds/does-not-exist')):
        response = client.get(url)
        out[key] = [response.status_code, payload in response.get_data(as_text=True)]

    for name in ('custom-aaa', 'custom-bbb', 'cuxx'):
        config = Config(name)
        config.makeDir()
        config.pathWithSuffix('.binds').write_text('<Root/>')
        config.pathWithNameAndSuffix('card', '.jpg').write_text('x')
        database.create_configuration(config_id=name, description=name)
    headers = {'Authorization': 'Basic ' + base64.b64encode(b'admin:probe-password').decode(),
               'Origin': 'http://localhost'}
    out['delete_status'] = client.post('/admin/configs/custom-aaa/delete', headers=headers).status_code
    out['remaining_files'] = sorted(p.name for p in Config('cuxx').path().parent.iterdir())
    out['remaining_rows'] = sorted(database.get_all_config_ids())
    out['traversal_status'] = client.post('/admin/configs/../delete', headers=headers).status_code
    out['configs_dir_alive'] = Config.configsPath().is_dir()

    response = client.get('/__probe', environ_base={'REMOTE_ADDR': '172.18.0.5'},
                          headers={'X-Forwarded-For': '203.0.113.9',
                                   'X-Forwarded-Proto': 'https', 'Host': 'cards.example'})
    out['proxy'] = json.loads(response.get_data(as_text=True))
    out['hsts'] = 'Strict-Transport-Security' in response.headers
    print('PROBE=' + json.dumps(out))
''')

APP_DEPENDENCIES = ('flask', 'flask_limiter', 'lxml', 'paramiko', 'requests', 'cryptography')


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in APP_DEPENDENCIES),
                     'application dependencies required')
class AppRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='edrefcard-app-probe-')
        env = {**os.environ, 'EDREFCARD_CONFIGS_DIR': cls.temp.name,
               'EDREFCARD_ADMIN_USER': 'admin', 'EDREFCARD_ADMIN_PASS': 'probe-password',
               'APP_ENV': 'development', 'APP_URL': ''}
        for name in ('ACCESS_TOKEN', 'TRUSTED_PROXY_HOPS'):
            env.pop(name, None)
        completed = subprocess.run([sys.executable, '-c', APP_PROBE, str(WWW)],
                                   capture_output=True, text=True, env=env, timeout=120)
        lines = [line for line in completed.stdout.splitlines() if line.startswith('PROBE=')]
        if not lines:
            raise AssertionError(f'probe failed:\n{completed.stdout}\n{completed.stderr}')
        cls.out = json.loads(lines[-1][len('PROBE='):])

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_error_pages_never_reflect_markup_and_answer_404(self):
        for key in ('binds', 'device', 'pdf', 'glob', 'unknown'):
            status, reflected = self.out[key]
            self.assertEqual(status, 404, key)
            self.assertFalse(reflected, key)

    def test_deleting_one_config_keeps_its_directory_siblings(self):
        self.assertEqual(self.out['delete_status'], 302)
        self.assertEqual(self.out['remaining_files'],
                         ['custom-bbb-card.jpg', 'custom-bbb.binds', 'cuxx-card.jpg', 'cuxx.binds'])
        self.assertEqual(self.out['remaining_rows'], ['custom-bbb', 'cuxx'])

    def test_delete_rejects_ids_that_are_not_generated_ids(self):
        self.assertIn(self.out['traversal_status'], (302, 404))
        self.assertTrue(self.out['configs_dir_alive'])

    def test_forwarded_headers_of_the_reverse_proxy_are_honoured(self):
        address, secure, url = self.out['proxy']
        self.assertEqual(address, '203.0.113.9')
        self.assertTrue(secure)
        self.assertEqual(url, 'https://cards.example/binds/x')
        self.assertTrue(self.out['hsts'])


if __name__ == '__main__':
    unittest.main()
