# Developer & Agent Guide

This document contains critical information about the architecture, quirks, and troubleshooting procedures for **EDRefCard**. Read this before attempting major refactors or debugging production issues.

## 🏗️ Architecture & Deployment

### Docker Split
The project uses two separate compose files:
*   **`docker-compose.yml`**: For **local development**. Runs with standard user permissions.
*   **`docker-compose.prod.yml`**: For **production**.
    *   **User**: Runs as `root` (`user: root`) to ensure write permissions on the mounted `configs` volume.
    *   **Env Vars**: Explicitly passes `EDREFCARD_ADMIN_USER`, `EDREFCARD_ADMIN_PASS`, and `APP_URL`.

### File Storage Structure
Configuration files are stored in `www/configs/` using a **hashed directory structure** to avoid filesystem limits:
*   Path format: `www/configs/{xx}/{run_id}.{ext}` (where `xx` are the first 2 chars of the run ID).
*   **Run ID**: Now primarily derived from the slugified filename (e.g., `my-setup`) with a random suffix for collisions.
*   **Example**: ID `unkbsa` is stored in `www/configs/un/unkbsa.binds`.


### 🗄️ Database & Persistence
*   **Engine**: SQLite.
*   **Location**: `www/configs/edrefcard.db`.
    *   *Critical*: The DB is located in `configs/` (mounted volume) and NOT `data/` or root. If moved to a non-mounted path, all data/stats will reset on container rebuild.


### 🧩 Application Structure (Refactoring v2.1)
*   **Blueprints**: The application has been refactored to use Flask Blueprints:
    *   `www/web.py`: Main user-facing routes (index, list, view, generate).
    *   `www/api.py`: Public JSON API (`/api/v1`).
    *   `www/admin/__init__.py`: Admin interface.
*   **Entry Point**: `www/app.py` initializes the app, registers blueprints, and handles configuration.
*   **Extensions**: Shared extensions (like `Limiter`) are in `www/extensions.py`.

## ⚠️ Known Quirks & Issues

### 1. Missing Templates & Unsupported Devices
*   **Scenario**: A configuration contains a controller for which no image template exists in `www/res/`.
*   **Behavior**: The system catches the `FileNotFoundError`, logs it, and continues rendering other devices. A warning is displayed to the user on the reference card page.
*   **Source missing**: If the `.binds` file is deleted from the server, the card cannot be regenerated.


### 2. Permissions on Volumes
*   Docker volumes on Linux/Prod often entail permission issues when writing generated images or logs.
*   **Solution**: Ensure the container runs as `root` in production, or carefully manage PUID/PGID matching host folder ownership. Current prod setup uses `user: root`.

### 3. ImageMagick / Wand
*   The application relies on `Wand` (ImageMagick binding).
*   If `Wand` is missing/broken, the app catches the `ImportError` and operates in a degraded mode (no image generation), logging the error to `www/configs/error.log`.

### 4. Download Links
*   When generating download links for `.binds` files, **always** include the subdirectory prefix.
    *   ❌ Incorrect: `url_for(..., path=f"{run_id}.binds")`
    *   ✅ Correct: `url_for(..., path=f"{run_id[:2]}/{run_id}.binds")`

## 🛠️ Debugging Tools

### Admin Debug Panel (`/admin/debug`)
Use this hidden route to investigate the production environment without shell access:
*   **File Browser**: Check existence of files in `configs/` (supports subdirectories like `ck/`).
*   **Logs**: View the tail of `www/configs/error.log`.
*   **Wand Status**: Check if the image renderer library is loaded correctly.

### Logging
*   **Persistent Log**: `www/configs/error.log`. Writes explicitly to disk (unlike stdout which can be lost in rotation).
*   **Memory Buffer**: Last ~50 errors are kept in memory and visible on the Debug page.

## 📝 Common Tasks

### Adding a New Device
1.  Add entry to `scripts/bindingsData.py` (`supportedDevices`).
2.  If it's a new `Template`, ensure the `.jpg` background exists in `www/images/`.
3.  Restart app (or reload if in dev mode).

### Restoring Database
If the SQLite DB is corrupted or lost, data can only be recovered if backups exist. Legacy pickle migration is no longer supported as of v2.2.


---

## 🌍 Language Policy

**ALL code, comments, documentation, and commit messages MUST be in English.**

### Why English-only?
- ✅ Collaboration with upstream (international project)
- ✅ Better tooling support (linters, IDEs, AI assistants)
- ✅ Consistency across the codebase
- ✅ Easier for future contributors

### What must be in English?
- Code files (`.py`, `.js`, `.html`, etc.)
- Comments in code
- Commit messages
- Documentation files (`.md`, docstrings)
- Configuration files (`docker-compose.yml`, etc.)
- Variable names and function names

### Exceptions
- User-facing strings that need translation (use i18n)
- Personal local files in `.gitignore` (e.g., `WORKFLOW.md` for personal use)

### Examples

#### ❌ Bad (French)
```python
# Génère une carte de référence
def generer_carte(config):
    # Code...
```

#### ✅ Good (English)
```python
# Generates a reference card
def generate_card(config):
    # Code...
```
