"""The staging password gate: inactive by default, closed when ACCESS_TOKEN is set."""
import os
import unittest
from unittest.mock import patch

from flask import Flask

import staging_gate

TOKEN = 'test-token-not-a-real-secret'


def make_app():
    app = Flask(__name__)
    staging_gate.register(app)

    @app.route('/')
    def home():
        return 'home'

    @app.route('/binds/<run_id>')
    def binds(run_id):
        return f'binds {run_id}'

    @app.route('/api/generate', methods=['POST'])
    def api():
        return 'api'

    return app


class InactiveGateTests(unittest.TestCase):
    def test_without_token_every_route_stays_public(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop('ACCESS_TOKEN', None)
            client = make_app().test_client()
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('X-Robots-Tag', response.headers)
            self.assertEqual(client.post('/api/generate').status_code, 200)


class ActiveGateTests(unittest.TestCase):
    def setUp(self):
        staging_gate._failures.clear()
        self.env = patch.dict(os.environ, {'ACCESS_TOKEN': TOKEN})
        self.env.start()
        self.client = make_app().test_client()

    def tearDown(self):
        self.env.stop()

    def test_page_redirects_to_password_form_with_relative_location(self):
        response = self.client.get('/binds/abc?x=1')
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers['Location'], '/acces?suite=%2Fbinds%2Fabc%3Fx%3D1')
        self.assertEqual(response.headers['X-Robots-Tag'], 'noindex, nofollow, noarchive')

    def test_api_and_assets_are_refused_without_redirect(self):
        self.assertEqual(self.client.post('/api/generate').status_code, 403)
        self.assertEqual(self.client.get('/static/app.js').status_code, 403)

    def test_wrong_password_is_rejected(self):
        response = self.client.post('/acces', data={'cle': 'wrong', 'suite': '/'})
        self.assertEqual(response.status_code, 303)
        self.assertIn('erreur=1', response.headers['Location'])
        self.assertIsNone(self.client.get_cookie(staging_gate.COOKIE))

    def test_right_password_sets_secure_cookie_and_opens_the_site(self):
        response = self.client.post('/acces', data={'cle': TOKEN, 'suite': '/binds/abc'})
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers['Location'], '/binds/abc')
        cookie = response.headers['Set-Cookie']
        for flag in ('HttpOnly', 'Secure', 'SameSite=Lax'):
            self.assertIn(flag, cookie)
        self.client.set_cookie(staging_gate.COOKIE, TOKEN)
        self.assertEqual(self.client.get('/binds/abc').get_data(as_text=True), 'binds abc')

    def test_redirect_after_login_never_leaves_the_site(self):
        for target in ('https://evil.example', '//evil.example', '/\\evil.example',
                       '/\t/evil.example', 'evil.example', '/acces?suite=/'):
            with self.subTest(target=target):
                response = self.client.post('/acces', data={'cle': TOKEN, 'suite': target})
                self.assertEqual(response.headers['Location'], '/')

    def test_repeated_failures_are_throttled(self):
        for _ in range(staging_gate.MAX_FAILURES):
            self.client.post('/acces', data={'cle': 'wrong'})
        response = self.client.post('/acces', data={'cle': TOKEN})
        self.assertEqual(response.status_code, 429)

    def test_password_form_and_free_paths_are_reachable(self):
        self.assertEqual(self.client.get('/acces').status_code, 200)
        self.assertNotEqual(self.client.get('/robots.txt').status_code, 403)


if __name__ == '__main__':
    unittest.main()
