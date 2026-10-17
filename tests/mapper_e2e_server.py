"""Run the real app against disposable data, never against a deployed database.

Linux/server runtime: python tests/mapper_e2e_server.py --source-www www
The emitted state file is private and holds only generated test credentials.
Stop with Ctrl+C. The scratch folder is retained for failure investigation.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-www', type=Path, required=True)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=0)
    parser.add_argument('--public-url', default='')
    parser.add_argument('--state-file', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_www.resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix='edrefcard-mapper-e2e-'))
    www = root / 'www'
    shutil.copytree(source, www, ignore=shutil.ignore_patterns(
        'configs', 'data', '__pycache__', '*.pyc', 'res', 'fonts'))
    for name in ['res', 'fonts']:
        (www / name).symlink_to(source / name, target_is_directory=True)
    configs = root / 'configs'
    configs.mkdir(mode=0o700)
    nonce = secrets.token_hex(16)
    password = secrets.token_urlsafe(24)
    # Override inherited production credentials, scheduler and data paths.
    os.environ.update(EDREFCARD_CONFIGS_DIR=str(configs), APP_ENV='test',
        APP_URL=args.public_url or f'http://127.0.0.1:{args.port}',
        EDREFCARD_ADMIN_USER='ci-admin', EDREFCARD_ADMIN_PASS=password,
        FLASK_SECRET_KEY=secrets.token_urlsafe(48))
    sys.path.insert(0, str(www))
    from app import app
    from scripts import database
    from scripts.models import Config
    from PIL import Image, ImageDraw
    from werkzeug.serving import make_server

    profile = '<Root PresetName="CI pilot" MajorVersion="4" MinorVersion="2">' \
        '<PrimaryFire><Primary Device="TEST0001" Key="Joy_1"/></PrimaryFire>' \
        '<PitchAxisRaw><Binding Device="TEST0001" Key="Joy_YAxis"/>' \
        '<Inverted Value="0"/><Deadzone Value="0"/></PitchAxisRaw></Root>'
    config = Config('ci-profile')
    config.makeDir()
    config.pathWithSuffix('.binds').write_text(profile, encoding='utf-8')
    database.create_configuration('ci-profile', description='CI pilot',
        display_groups=['Ship'], devices={'TEST0001::0':None}, is_public=False)
    for version, color in [('original','#888888'), ('replacement','#555555')]:
        image = Image.new('RGB', (4400,2560), 'white')
        ImageDraw.Draw(image).ellipse((1900,700,2500,1800), fill=color)
        image.save(root / (version + '.png'))
    (root / 'ci-upload.binds').write_text(profile, encoding='utf-8')
    original_wsgi = app.wsgi_app

    def marked_app(environ, start_response):
        def marked_response(status, headers, exc_info=None):
            headers.append(('X-Edrefcard-Test-Instance', nonce))
            return start_response(status, headers, exc_info)
        return original_wsgi(environ, marked_response)

    app.wsgi_app = marked_app
    # Single process: this tests real routes/auth/SQLite, not gunicorn scaling.
    server = make_server(args.host, args.port, app)
    base = args.public_url or f'http://127.0.0.1:{server.server_port}'
    Config.setWebRoot(base + '/')
    app.config['SESSION_COOKIE_SECURE'] = base.startswith('https://')
    state = {'base_url':base, 'nonce':nonce, 'pid':os.getpid(), 'admin_password':password,
        'mapper_password':secrets.token_urlsafe(24), 'root':str(root)}
    args.state_file.parent.mkdir(parents=True, exist_ok=True)
    args.state_file.write_text(json.dumps(state), encoding='utf-8')
    args.state_file.chmod(0o600)
    print(json.dumps({'ready':True, 'state_file':str(args.state_file), 'base_url':base}), flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
