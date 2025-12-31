# EDRefCard

Elite: Dangerous has a great many command bindings to learn. To help with that, EDRefCard generates a printable reference card from your Elite: Dangerous bindings file.

Currently hosted at [https://edrefcard.info/](https://edrefcard.info/).

## Dependencies

* Python 3.10 or later
* Python modules (see `requirements.txt`):
  * `flask` - Web framework
  * `gunicorn` - WSGI HTTP server
  * `lxml` - XML parsing
  * `wand` - ImageMagick bindings
  * `pytest`, `pytest-cov` - Testing

* ImageMagick 6 or 7
  * You may need to configure the `MAGICK_HOME` env var to get `wand` to see the ImageMagick libraries.

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Flask development server
cd www
python app.py

# Access at http://localhost:5000
```

### Docker (Recommended)

Build and run with Docker:

```bash
docker build -t edrefcard .
docker run -d --rm --name edrefcard -p 8080:8000 edrefcard
```

Or with docker-compose:

```bash
docker-compose up -d
```

EDRefCard can then be accessed at http://localhost:8080

## Project Structure

```
edrefcard/
├── www/
│   ├── app.py              # Flask application entry point
│   ├── templates/          # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── refcard.html
│   │   ├── list.html
│   │   ├── devices.html
│   │   └── error.html
│   ├── scripts/
│   │   ├── bindings.py     # Core binding parsing logic
│   │   ├── bindingsData.py # Device definitions
│   │   └── controlsData.py # Control mappings
│   ├── configs/            # Generated configurations (created at runtime)
│   ├── res/                # Image templates for devices
│   ├── fonts/              # Font files
│   └── ed.css              # Stylesheet
├── bindings/               # Test binding files
├── Dockerfile
├── docker-compose.yaml
└── requirements.txt
```

## API Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Home page with upload form |
| `/generate` | POST | Upload .binds file and generate reference card |
| `/list` | GET | List all public configurations |
| `/binds/<id>` | GET | View a saved configuration |
| `/devices` | GET | List all supported controllers |
| `/device/<name>` | GET | View a device's button layout |
| `/configs/<path>` | GET | Static files (generated images) |

## Configuration

The application can be configured via environment variables or by modifying the Flask app configuration in `www/app.py`:

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHONIOENCODING` | Character encoding | `utf-8` |

## Supported Controllers

EDRefCard supports 68+ controllers including:
- Thrustmaster (T16000M, HOTAS Warthog, T-Flight, etc.)
- Logitech (Extreme 3D Pro, X52, X56, etc.)
- VKB (Gladiator, Kosmosima, etc.)
- Virpil (WarBRD, Alpha, MongoosT, etc.)
- CH Products (Fighterstick, Pro Throttle, etc.)
- Xbox 360 / PlayStation controllers
- Standard keyboard

See the full list at `/devices` on the running application.

## Admin Panel

EDRefCard v2.0 includes a built-in admin panel for managing configurations and devices.

### Access
- URL: `/admin/`
- Authentication: HTTP Basic Auth

### Configuration
Set the following environment variables to configure admin access:

| Variable | Description | Default |
|----------|-------------|---------|
| `EDREFCARD_ADMIN_USER` | Admin username | `admin` |
| `EDREFCARD_ADMIN_PASS` | Admin password | `changeme` |
| `FLASK_SECRET_KEY` | Secret key for sessions | `dev-secret-key...` |

### Features
- **Dashboard**: View statistics on configuration usage and popular devices
- **Configurations**: List, search, delete, and toggle visibility of user configurations
- **Devices**: View list of supported devices and their template mappings
- **Data Migration**: Tool to import legacy pickle files into the SQLite database

## Data Storage

EDRefCard v2.0 uses a hybrid storage approach:
- **SQLite Database (`edrefcard.db`)**: Stores configuration metadata (id, description, status, devices used).
- **Filesystem**: Stores generated images (`.jpg`) and original bindings files (`.binds`) in the `configs/` directory.

When upgrading from v1.0, use the `/admin/migrate` tool to import existing pickle files into the database.

## Development

### Running Tests

```bash
pytest --cov=. --cov-report term-missing
```

### Adding New Controllers

1. Add device definition to `www/scripts/bindingsData.py`
2. Add button/axis image template to `www/res/`
3. Run tests to validate

## Credits

EDRefCard is derived with permission from code originally developed by CMDR jgm.

## License

See [LICENSE](LICENSE) file.
