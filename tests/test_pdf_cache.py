"""Verify real PDF cache invalidation and atomic output in temporary folders."""
import ast
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    import fitz
    from fpdf import FPDF
    from PIL import Image
    AVAILABLE=hasattr(fitz,'open')
except ImportError:
    AVAILABLE=False

ROOT=Path(__file__).resolve().parents[1]


@unittest.skipUnless(AVAILABLE,'PyMuPDF, fpdf2 and Pillow required')
class PdfCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='edrefcard-pdf-cache-')
        self.root=Path(self.temp.name)
        self.folder=self.root/'te';self.folder.mkdir()
        self.logs=[]
        tree=ast.parse((ROOT/'www/web.py').read_text(encoding='utf-8'))
        node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='generate_pdf')
        self.env={'Path':Path,'os':os,'tempfile':tempfile,'logError':self.logs.append,
            'current_app':SimpleNamespace(config={'CONFIGS_FOLDER':self.root})}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'actual-pdf-helper','exec'),self.env)
        self.image=self.folder/'test-card-device.jpg'
        Image.new('RGB',(600,400),'red').save(self.image)

    def tearDown(self):
        self.temp.cleanup()

    def generate(self,fmt='A4'):
        return self.env['generate_pdf']('test-card',fmt)

    def metadata(self,path):
        with fitz.open(path) as pdf:
            self.assertTrue(pdf[0].get_images())
            return pdf.metadata['keywords'],len(pdf)

    def test_unchanged_inputs_reuse_cache_and_touch_does_not_invalidate(self):
        for fmt in ['A4','Letter']:
            with self.subTest(format=fmt):
                path=Path(self.generate(fmt))
                self.assertTrue(self.metadata(path)[0].startswith('edrefcard-source-sha256='))
                original=path.read_bytes();mtime=path.stat().st_mtime_ns
                os.utime(self.image,ns=(self.image.stat().st_atime_ns,self.image.stat().st_mtime_ns+1_000_000))
                self.assertEqual(self.generate(fmt),str(path))
                self.assertEqual(path.read_bytes(),original)
                self.assertEqual(path.stat().st_mtime_ns,mtime)
        self.assertEqual(self.logs,[])

    def test_content_change_with_identical_size_and_mtime_invalidates(self):
        self.image.write_bytes(self.image.read_bytes()+b'marker A')
        path=Path(self.generate())
        old=self.metadata(path)[0];stat=self.image.stat()
        content=self.image.read_bytes()
        self.image.write_bytes(content[:-1]+b'B')
        os.utime(self.image,ns=(stat.st_atime_ns,stat.st_mtime_ns))
        self.assertEqual(self.image.stat().st_size,stat.st_size)
        self.generate()
        self.assertNotEqual(self.metadata(path)[0],old)

    def test_added_and_removed_images_update_page_count(self):
        path=Path(self.generate());self.assertEqual(self.metadata(path)[1],1)
        extra=self.folder/'test-card-another.jpg'
        Image.new('RGB',(600,400),'blue').save(extra)
        self.generate();self.assertEqual(self.metadata(path)[1],2)
        extra.unlink()
        self.generate();self.assertEqual(self.metadata(path)[1],1)

    def test_keyboard_remains_last_page(self):
        keyboard=self.folder/'test-card-keyboard.jpg'
        Image.new('RGB',(600,400),'green').save(keyboard)
        path=self.generate()
        with fitz.open(path) as pdf:
            self.assertEqual(len(pdf),2)
            first=pdf[0].get_pixmap();last=pdf[1].get_pixmap()
            self.assertGreater(first.pixel(first.width//2,first.height//2)[0],200)
            self.assertGreater(last.pixel(last.width//2,last.height//2)[1],100)

    def test_legacy_and_damaged_cache_are_replaced(self):
        path=self.folder/'test-card-A4.pdf'
        for content in [b'old cache without metadata',b'%PDF-invalid']:
            with self.subTest(content=content):
                path.write_bytes(content)
                self.generate()
                self.assertEqual(self.metadata(path)[1],1)
        pdf=FPDF();pdf.add_page();pdf.set_font('Helvetica',size=12);pdf.text(10,20,'Legacy PDF')
        pdf.output(str(path))
        self.generate()
        self.assertTrue(self.metadata(path)[0].startswith('edrefcard-source-sha256='))

    def test_failed_image_never_overwrites_last_good_cache(self):
        path=Path(self.generate());original=path.read_bytes()
        (self.folder/'test-card-broken.jpg').write_bytes(b'not a JPEG')
        self.assertIsNone(self.generate())
        self.assertEqual(path.read_bytes(),original)
        self.assertTrue(any('Error adding image' in log for log in self.logs))

    def test_failed_pdf_write_is_atomic_and_temp_output_is_cleaned(self):
        path=Path(self.generate());original=path.read_bytes()
        self.image.write_bytes(self.image.read_bytes()+b'changed')
        with patch.object(FPDF,'output',side_effect=OSError('write unavailable')):
            self.assertIsNone(self.generate())
        self.assertEqual(path.read_bytes(),original)
        self.assertEqual(set(p.name for p in self.folder.iterdir()),{path.name,self.image.name})

    def test_concurrent_exports_produce_one_complete_valid_cache(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            outputs=list(executor.map(lambda _:self.generate(),range(4)))
        self.assertTrue(all(path==outputs[0] for path in outputs))
        self.assertEqual(self.metadata(outputs[0])[1],1)
        self.assertEqual(self.logs,[])

    def test_missing_all_sources_does_not_serve_stale_pdf(self):
        path=Path(self.generate());original=path.read_bytes()
        self.image.unlink()
        self.assertIsNone(self.generate())
        self.assertEqual(path.read_bytes(),original)


if __name__=='__main__':
    unittest.main()
