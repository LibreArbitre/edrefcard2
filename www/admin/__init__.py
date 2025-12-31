#!/usr/bin/env python3
"""
EDRefCard Admin Blueprint

Flask Blueprint for administration functionality.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import shutil
from pathlib import Path

from .auth import require_admin

# Create blueprint
admin_bp = Blueprint('admin', __name__, 
                     url_prefix='/admin',
                     template_folder='templates')


# Import database lazily to avoid circular imports
def get_db_module():
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
    from scripts import database
    return database


@admin_bp.route('/')
@require_admin
def dashboard():
    """Admin dashboard with statistics."""
    db = get_db_module()
    stats = db.get_configuration_stats()
    return render_template('admin/dashboard.html', stats=stats)


@admin_bp.route('/configs')
@require_admin
def list_configs():
    """List all configurations with pagination."""
    db = get_db_module()
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    device = request.args.get('device', '')
    public_only = request.args.get('public_only', '0') == '1'
    
    configs, total = db.list_configurations(
        page=page,
        per_page=50,
        public_only=public_only,
        search=search if search else None,
        device_filter=device if device else None
    )
    
    total_pages = (total + 49) // 50
    
    return render_template('admin/configs.html',
                           configs=configs,
                           page=page,
                           total_pages=total_pages,
                           total=total,
                           search=search,
                           device=device,
                           public_only=public_only)


@admin_bp.route('/configs/<config_id>/delete', methods=['POST'])
@require_admin
def delete_config(config_id):
    """Delete a configuration."""
    db = get_db_module()
    
    # Get config path to delete files
    from scripts.models import Config
    config = Config(config_id)
    config_path = config.path().parent
    
    # Delete from database
    db.delete_configuration(config_id)
    
    # Delete files on disk
    if config_path.exists():
        try:
            shutil.rmtree(config_path)
        except Exception as e:
            flash(f'Warning: Could not delete files: {e}', 'warning')
    
    flash(f'Configuration {config_id} deleted.', 'success')
    return redirect(url_for('admin.list_configs'))


@admin_bp.route('/configs/<config_id>/purge-pdf', methods=['POST'])
@require_admin
def purge_pdf(config_id):
    """Purge generated PDF files for a configuration."""
    from scripts.models import Config
    config = Config(config_id)
    config_path = config.path().parent
    
    purged_count = 0
    errors = []
    
    # Look for PDF files in the config directory
    if config_path.exists():
        for pdf_file in config_path.glob('*.pdf'):
            try:
                pdf_file.unlink()
                purged_count += 1
            except Exception as e:
                errors.append(f"Could not delete {pdf_file.name}: {e}")
    
    if errors:
        flash(f'Purged {purged_count} PDFs, but encountered errors: {"; ".join(errors)}', 'warning')
    elif purged_count > 0:
        flash(f'Successfully purged {purged_count} PDF files for {config_id}.', 'success')
    else:
        flash(f'No PDF files found to purge for {config_id}.', 'info')
        
    return redirect(url_for('admin.list_configs'))


@admin_bp.route('/configs/<config_id>/edit', methods=['POST'])
@require_admin
def edit_config(config_id):
    """Edit a configuration's description or visibility."""
    db = get_db_module()
    
    description = request.form.get('description', '')
    is_public = request.form.get('is_public') == 'on'
    is_featured = request.form.get('is_featured') == 'on'
    
    db.update_configuration(
        config_id,
        description=description,
        is_public=1 if is_public else 0,
        is_featured=1 if is_featured else 0
    )
    
    flash(f'Configuration {config_id} updated.', 'success')
    return redirect(url_for('admin.list_configs'))


@admin_bp.route('/configs/<config_id>/toggle-public', methods=['POST'])
@require_admin
def toggle_public(config_id):
    """Toggle a configuration's public status."""
    db = get_db_module()
    
    config = db.get_configuration(config_id)
    if config:
        new_status = 0 if config['is_public'] else 1
        db.update_configuration(config_id, is_public=new_status)
        status = 'public' if new_status else 'private'
        flash(f'Configuration {config_id} is now {status}.', 'success')
    
    return redirect(url_for('admin.list_configs'))


@admin_bp.route('/devices')
@require_admin
def list_devices():
    """List all supported devices."""
    from scripts.bindingsData import supportedDevices
    
    # Sort devices by name
    devices = sorted(supportedDevices.items(), key=lambda x: x[0])
    
    return render_template('admin/devices.html', devices=devices)


@admin_bp.route('/migrate', methods=['GET', 'POST'])
@require_admin
def migrate_data():
    """Migrate pickle files to SQLite."""
    db = get_db_module()
    
    if request.method == 'POST':
        from scripts.models import Config
        configs_path = Config.configsPath()
        
        migrated, errors = db.migrate_from_pickle(configs_path)
        
        flash(f'Migration complete: {migrated} migrated, {errors} errors.', 
              'success' if errors == 0 else 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # GET: show migration form
    from scripts.models import Config
    configs_path = Config.configsPath()
    
    # Get all replay files
    replay_files = list(configs_path.glob('**/*.replay')) if configs_path.exists() else []
    total_pickles = len(replay_files)
    
    # Get all DB IDs
    db_ids = db.get_all_config_ids()
    
    # Calculate missing
    missing_count = 0
    for p in replay_files:
        if p.stem not in db_ids:
            missing_count += 1
            
    return render_template('admin/migrate.html', 
                           pickle_count=missing_count,
                           total_pickles=total_pickles)


@admin_bp.route('/stats')
@require_admin
def stats():
    """Detailed statistics page."""
    db = get_db_module()
    stats = db.get_configuration_stats()
    device_names = db.get_all_device_names()
    
    return render_template('admin/stats.html', stats=stats, device_names=device_names)


@admin_bp.route('/debug')
@require_admin
def debug_info():
    """Debug information about the environment."""
    import sys
    import shutil
    from scripts.models import Config
    from scripts.utils import RECENT_ERRORS
    
    # Check Wand status
    wand_status = "Not Installed"
    wand_path = "Unknown"
    wand_error = None
    try:
        import wand
        from wand.version import VERSION
        wand_status = f"Installed (v{VERSION})"
        wand_path = wand.__file__
    except ImportError as e:
        wand_status = "Import Failed"
        wand_error = str(e)
    
    # Path info
    www_dir = Path(__file__).parent.parent
    configs_path = Config.configsPath()
    
    # Directory listing
    config_files = []
    subdir = request.args.get('subdir')
    
    list_path = configs_path
    if subdir:
        list_path = configs_path / subdir
        
    if list_path.exists():
        try:
            # List top level standard dirs or files
            for p in sorted(list_path.glob('*')):
                config_files.append(f"{p.name} ({'DIR' if p.is_dir() else 'FILE'})")
        except Exception as e:
            config_files.append(f"Error listing files: {e}")
    else:
        config_files.append(f"Directory {list_path} does not exist!")

    # Read persistent log file
    persistent_logs = []
    try:
        log_path = Path(__file__).parent.parent / 'configs' / 'error.log'
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                # Read last 50 lines
                lines = f.readlines()
                persistent_logs = lines[-50:]
                persistent_logs.reverse() # Show newest first
    except Exception as e:
        persistent_logs = [f"Error reading log file: {e}"]
        
    return render_template('admin/debug.html',
                           www_dir=www_dir,
                           configs_path=configs_path,
                           wand_status=wand_status,
                           wand_path=wand_path,
                           wand_error=wand_error,
                           config_files=config_files,
                           sys_path=sys.path,
                           recent_errors=RECENT_ERRORS,
                           persistent_logs=persistent_logs,
                           subdir=subdir)
