"""Canonical generated links must not inherit the proxy's internal scheme."""
import ast
import os
from pathlib import Path
import random
import string
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.parse import urljoin


class WebRootTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).resolve().parents[1] / 'www/scripts/models.py'
        tree = ast.parse(source.read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Config')
        scope = dict(os=os, Path=Path, string=string, random=random, urljoin=urljoin)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
        self.config = scope['Config']

    def test_configured_external_origin_wins_over_internal_proxy_request(self):
        self.config.setWebRoot('https://edrefcard2-dev.l0l.fr/')
        flask = SimpleNamespace(has_request_context=lambda: True,
                                request=SimpleNamespace(url_root='http://edrefcard2-dev.l0l.fr/'))
        with patch.dict(sys.modules, {'flask': flask}):
            self.assertEqual(self.config.webRoot(), 'https://edrefcard2-dev.l0l.fr/')

    def test_unconfigured_root_can_use_request_origin(self):
        flask = SimpleNamespace(has_request_context=lambda: True,
                                request=SimpleNamespace(url_root='http://localhost:8080/'))
        with patch.dict(sys.modules, {'flask': flask}):
            self.assertEqual(self.config.webRoot(), 'http://localhost:8080/')

    def test_unconfigured_root_outside_request_uses_environment(self):
        flask = SimpleNamespace(has_request_context=lambda: False)
        with patch.dict(sys.modules, {'flask': flask}), patch.dict(
                os.environ, {'SCRIPT_URI': 'https://example.test/'}):
            self.assertEqual(self.config.webRoot(), 'https://example.test/')


if __name__ == '__main__':
    unittest.main()
