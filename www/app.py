#!/usr/bin/env python3
"""
EDRefCard Flask Application

This module provides the Flask web application for generating Elite: Dangerous
reference cards from controller bindings files.
"""

import os
import sys
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, send_from_directory

# Get the www directory path
WWW_DIR = Path(__file__).parent.resolve()

# Add scripts directory to path for imports
scripts_path = WWW_DIR / 'scripts'
sys.path.insert(0, str(scripts_path))

# Import from the modular package
from scripts import (
    __version__,
    Config,
    Mode,
    Errors,
    supportedDevices,
    groupStyles,
    parseBindings,
    parseFormData,
    createHOTASImage,
    appendKeyboardImage,
    createBlockImage,
    saveReplayInfo,
    controllerNames,
    logError,
)

app = Flask(__name__, 
            static_folder=str(WWW_DIR), 
            static_url_path='',
            template_folder=str(WWW_DIR / 'templates'))

# Configure the application
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['CONFIGS_FOLDER'] = WWW_DIR / 'configs'
app.config['WWW_DIR'] = WWW_DIR
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure the bindings Config class for Flask
# Configure the bindings Config class for Flask
Config.setDirRoot(WWW_DIR)
web_root = os.environ.get('SCRIPT_URI', 'http://localhost:8080/')
if not web_root.endswith('/'):
    web_root += '/'
Config.setWebRoot(web_root)
print(f"Application configured with Web Root: {web_root}")

# Initialize SQLite database
# Initialize SQLite database
from scripts.database import init_db, get_configuration_stats, migrate_from_pickle
DB_PATH = WWW_DIR / 'data' / 'edrefcard.db'
init_db(DB_PATH)

# Auto-migrate legacy data if database is empty
try:
    stats = get_configuration_stats()
    if stats['total_configurations'] == 0:
        print("Database empty. Checking for legacy configurations to migrate...")
        configs_dir = WWW_DIR / 'configs'
        if configs_dir.exists():
            migrated, errors = migrate_from_pickle(configs_dir)
            if migrated > 0:
                print(f"Auto-migrated {migrated} legacy configurations ({errors} errors).")
            else:
                print("No legacy configurations found.")
except Exception as e:
    print(f"Warning: Auto-migration check failed: {e}")

# Register admin blueprint
from admin import admin_bp
app.register_blueprint(admin_bp)

# Register CLI commands
# Register CLI commands
from commands import clean_cache_command, find_unsupported_command, migrate_legacy_command, import_defaults_command
app.cli.add_command(clean_cache_command)
app.cli.add_command(find_unsupported_command)
app.cli.add_command(migrate_legacy_command)
app.cli.add_command(import_defaults_command)


def get_configs_path():
    """Get the path to the configs directory."""
    return app.config['CONFIGS_FOLDER']


@app.before_request
def set_working_directory():
    """Set working directory for image generation paths."""
    os.chdir(app.config['WWW_DIR'] / 'scripts')


@app.context_processor
def inject_version():
    """Inject version into all templates."""
    return {'version': __version__}


@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    """Process uploaded bindings file and generate reference cards."""
    errors = Errors()
    
    # Check description validity
    description = request.form.get('description', '')
    if len(description) > 0 and not description[0].isalnum():
        return render_template('error.html', 
                               error_message='That is not a valid description. Leading punctuation is not allowed.')
    
    # Check for uploaded file
    if 'bindings' not in request.files:
        return render_template('error.html',
                               error_message='<h1>No bindings file supplied; please go back and select your binds file as per the instructions.</h1>')
    
    file = request.files['bindings']
    if file.filename == '':
        return render_template('error.html',
                               error_message='<h1>No bindings file supplied; please go back and select your binds file as per the instructions.</h1>')
    
    # Parse form options
    display_groups = parseFormData(request.form)
    styling = 'None'
    if request.form.get('styling') == 'group':
        styling = 'Group'
    elif request.form.get('styling') == 'category':
        styling = 'Category'
    elif request.form.get('styling') == 'modifier':
        styling = 'Modifier'
    
    # Create new config
    config = Config.newRandom()
    config.makeDir()
    run_id = config.name
    
    # Read and save bindings file
    try:
        xml = file.read().decode('utf-8')
    except UnicodeDecodeError:
        return render_template('error.html',
                               error_message='<h1>Could not decode the bindings file. Please ensure it is a valid XML file.</h1>')
    
    binds_path = config.pathWithSuffix('.binds')
    with open(str(binds_path), 'w', encoding='utf-8') as f:
        f.write(xml)
    
    public = len(description) > 0
    
    # Parse bindings and generate images
    (physical_keys, modifiers, devices) = parseBindings(run_id, xml, display_groups, errors)
    
    already_handled_devices = []
    created_images = []
    
    for supported_device_key, supported_device in supportedDevices.items():
        if supported_device_key == 'Keyboard':
            continue
        
        for device_index in [0, 1]:
            handled = False
            device_key = None
            for handled_device in supported_device.get('KeyDevices', supported_device.get('HandledDevices')):
                if handled_device.find('::') > -1:
                    if device_index == int(handled_device.split('::')[1]) and devices.get(handled_device) is not None:
                        handled = True
                        device_key = handled_device
                        break
                else:
                    if devices.get(f'{handled_device}::{device_index}') is not None:
                        handled = True
                        device_key = f'{handled_device}::{device_index}'
                        break
            
            if handled:
                has_new_bindings = False
                for device in supported_device.get('KeyDevices', supported_device.get('HandledDevices')):
                    if device_key not in already_handled_devices:
                        has_new_bindings = True
                        break
                
                if has_new_bindings:
                    createHOTASImage(
                        physical_keys, modifiers, 
                        supported_device['Template'], 
                        supported_device['HandledDevices'], 
                        40, config, public, styling, device_index, 
                        errors.misconfigurationWarnings
                    )
                    created_images.append(f'{supported_device_key}::{device_index}')
                    for handled_device in supported_device['HandledDevices']:
                        already_handled_devices.append(f'{handled_device}::{device_index}')
    
    if devices.get('Keyboard::0') is not None:
        appendKeyboardImage(created_images, physical_keys, modifiers, display_groups, run_id, public)
    
    # Check for unsupported devices
    for device_key, device in devices.items():
        ignored_devices = ['Mouse::0', 'ArduinoLeonardo::0', 'vJoy::0', 'vJoy::1', '16D00AEA::0']
        if device is None and device_key not in ignored_devices:
            logError(f'{run_id}: found unsupported device {device_key}\n')
            if errors.unhandledDevicesWarnings == '':
                errors.unhandledDevicesWarnings = f'<h1>Unknown controller detected</h1>You have a device that is not supported at this time. Please report details of your device by following the link at the bottom of this page supplying the reference "{run_id}" and we will attempt to add support for it.'
        if device is not None and 'ThrustMasterWarthogCombined' in device['HandledDevices'] and errors.deviceWarnings == '':
            errors.deviceWarnings = '<h2>Mapping Software Detected</h2>You are using the ThrustMaster TARGET software. As a result it is possible that not all of the controls will show up. If you have missing controls then you should remove the mapping from TARGET and map them using Elite\'s own configuration UI.'
    
    if len(created_images) == 0 and not errors.misconfigurationWarnings and not errors.unhandledDevicesWarnings and not errors.errors:
        errors.errors = '<h1>The file supplied does not have any bindings for a supported controller or keyboard.</h1>'
    
    # Save replay info if public
    if public:
        saveReplayInfo(config, description, styling, display_groups, devices, errors)
    
    return render_template('refcard.html',
                           run_id=run_id,
                           errors={
                               'unhandled_devices_warnings': errors.unhandledDevicesWarnings,
                               'misconfiguration_warnings': errors.misconfigurationWarnings,
                               'device_warnings': errors.deviceWarnings,
                               'errors': errors.errors,
                           },
                           created_images=created_images,
                           device_for_block_image=None,
                           public=public,
                           refcard_url=config.refcardURL(),
                           binds_url=config.bindsURL(),
                           supported_devices=supportedDevices)


@app.route('/list')
def list_configs():
    """List all public configurations."""
    device_filters = request.args.getlist('deviceFilter')
    selected_controllers = set(device_filters) if device_filters else set()
    
    search_opts = {'controllers': selected_controllers} if selected_controllers else {}
    
    objs = Config.allConfigs(sortKey=lambda obj: str(obj['description']).casefold())
    
    items = []
    for obj in objs:
        try:
            config = Config(obj['runID'])
            name = str(obj['description'])
            if name == '':
                continue
            
            controllers = controllerNames(obj)
            
            # Apply filter if provided
            if selected_controllers:
                requested_devices = []
                for controller in selected_controllers:
                    device_info = supportedDevices.get(controller, {})
                    requested_devices.extend(device_info.get('HandledDevices', []))
                requested_devices_set = set(requested_devices)
                
                devices = [full_key.split('::')[0] for full_key in obj['devices'].keys()]
                if not any(rd in devices for rd in requested_devices_set):
                    continue
            
            items.append({
                'url': config.refcardURL(),
                'description': name,
                'controllers': ', '.join(sorted(controllers)),
                'date': str(obj['timestamp'].ctime()),
            })
        except Exception as e:
            logError(f'Error processing item {obj.get("runID", "unknown")}: {e}\n')
            continue
    
    controllers = sorted(supportedDevices.keys())
    
    return render_template('list.html',
                           controllers=controllers,
                           selected_controllers=selected_controllers,
                           search_opts=search_opts,
                           items=items)


@app.route('/binds/<run_id>')
def show_binds(run_id):
    """Show a saved configuration."""
    import codecs
    import pickle
    
    errors = Errors()
    
    try:
        config = Config(run_id)
        binds_path = config.pathWithSuffix('.binds')
        replay_path = config.pathWithSuffix('.replay')
        
        if not binds_path.exists():
            raise FileNotFoundError
        
        with codecs.open(str(binds_path), 'r', 'utf-8') as f:
            xml = f.read()
        
        display_groups = ['Galaxy map', 'General', 'Head look', 'SRV', 'Ship', 'UI']
        styling = 'None'
        description = ''
        
        if replay_path.exists():
            with replay_path.open('rb') as pickle_file:
                replay_info = pickle.load(pickle_file)
                display_groups = replay_info.get('displayGroups', display_groups)
                errors.misconfigurationWarnings = replay_info.get('misconfigurationWarnings', replay_info.get('warnings', ''))
                errors.deviceWarnings = replay_info.get('deviceWarnings', '')
                styling = replay_info.get('styling', 'None')
                description = replay_info.get('description', '')
    except (ValueError, FileNotFoundError):
        return render_template('error.html',
                               error_message=f'<h1>Configuration "{run_id}" not found</h1>')
    
    # Parse and generate
    (physical_keys, modifiers, devices) = parseBindings(run_id, xml, display_groups, errors)
    
    already_handled_devices = []
    created_images = []
    
    for supported_device_key, supported_device in supportedDevices.items():
        if supported_device_key == 'Keyboard':
            continue
        
        for device_index in [0, 1]:
            handled = False
            device_key = None
            for handled_device in supported_device.get('KeyDevices', supported_device.get('HandledDevices')):
                if handled_device.find('::') > -1:
                    if device_index == int(handled_device.split('::')[1]) and devices.get(handled_device) is not None:
                        handled = True
                        device_key = handled_device
                        break
                else:
                    if devices.get(f'{handled_device}::{device_index}') is not None:
                        handled = True
                        device_key = f'{handled_device}::{device_index}'
                        break
            
            if handled:
                has_new_bindings = False
                for device in supported_device.get('KeyDevices', supported_device.get('HandledDevices')):
                    if device_key not in already_handled_devices:
                        has_new_bindings = True
                        break
                
                if has_new_bindings:
                    createHOTASImage(
                        physical_keys, modifiers,
                        supported_device['Template'],
                        supported_device['HandledDevices'],
                        40, config, True, styling, device_index,
                        errors.misconfigurationWarnings
                    )
                    created_images.append(f'{supported_device_key}::{device_index}')
                    for handled_device in supported_device['HandledDevices']:
                        already_handled_devices.append(f'{handled_device}::{device_index}')
    
    if devices.get('Keyboard::0') is not None:
        appendKeyboardImage(created_images, physical_keys, modifiers, display_groups, run_id, True)
    
    return render_template('refcard.html',
                           run_id=run_id,
                           errors={
                               'unhandled_devices_warnings': errors.unhandledDevicesWarnings,
                               'misconfiguration_warnings': errors.misconfigurationWarnings,
                               'device_warnings': errors.deviceWarnings,
                               'errors': errors.errors,
                           },
                           created_images=created_images,
                           device_for_block_image=None,
                           public=True,
                           refcard_url=config.refcardURL(),
                           binds_url=config.bindsURL(),
                           supported_devices=supportedDevices)


@app.route('/devices')
def list_devices():
    """List all supported devices."""
    devices = []
    for name in sorted(supportedDevices.keys()):
        devices.append({
            'name': name,
            'handled_devices': supportedDevices[name]['HandledDevices'],
        })
    
    return render_template('devices.html', devices=devices)


@app.route('/device/<device_name>')
def show_device(device_name):
    """Show a device's button layout."""
    try:
        createBlockImage(device_name)
    except KeyError:
        return render_template('error.html',
                               error_message=f'<h1>{device_name} is not a supported controller.</h1>')
    
    template_name = supportedDevices[device_name]['Template']
    
    return render_template('refcard.html',
                           run_id='',
                           errors={
                               'unhandled_devices_warnings': '',
                               'misconfiguration_warnings': '',
                               'device_warnings': '',
                               'errors': '',
                           },
                           created_images=[],
                           device_for_block_image=device_name,
                           public=False,
                           refcard_url='',
                           binds_url='',
                           supported_devices=supportedDevices)


@app.route('/configs/<path:path>')
def serve_config(path):
    """Serve generated configuration images and files."""
    configs_folder = get_configs_path()
    return send_from_directory(configs_folder, path)

@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    """Serve script files."""
    return send_from_directory(scripts_path, filename)

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files."""
    # print(f"DEBUG: serve_static called with filename={filename}")
    try:
        return send_from_directory(WWW_DIR, filename)
    except Exception as e:
        # print(f"DEBUG: serve_static error for {filename}: {e}")
        raise e


# Serve CSS file
@app.route('/ed.css')
def serve_css():
    """Serve the main CSS file."""
    return send_from_directory(WWW_DIR, 'ed.css')


# Serve favicon
@app.route('/favicon.ico')
def serve_favicon():
    """Serve the favicon."""
    return send_from_directory(WWW_DIR, 'favicon.ico')


# Serve fonts
@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    """Serve font files."""
    return send_from_directory(WWW_DIR / 'fonts', filename)


# Serve res (resources like images)
@app.route('/res/<path:filename>')
def serve_res(filename):
    """Serve resource files."""
    return send_from_directory(WWW_DIR / 'res', filename)


if __name__ == '__main__':
    # Ensure configs directory exists
    configs_path = get_configs_path()
    configs_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting EDRefCard v{__version__}")
    print(f"WWW directory: {WWW_DIR}")
    print(f"Configs directory: {configs_path}")
    
    app.run(debug=True, host='0.0.0.0', port=8080)
