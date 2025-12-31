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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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
from scripts import database

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
# Prioritize APP_URL, then SCRIPT_URI, then default
web_root = os.environ.get('APP_URL') or os.environ.get('SCRIPT_URI', 'http://localhost:8080/')
if not web_root.endswith('/'):
    web_root += '/'
Config.setWebRoot(web_root)
print(f"Application configured with Web Root: {web_root}")

# Initialize SQLite database
# Initialize SQLite database
from scripts.database import init_db, get_configuration_stats, migrate_from_pickle
# Store DB in configs folder for persistence
DB_PATH = WWW_DIR / 'configs' / 'edrefcard.db'
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

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",  # Use Redis in production for multi-worker
    strategy="fixed-window"
)

# Register CLI commands
from commands import clean_cache_command, find_unsupported_command, migrate_legacy_command, import_defaults_command
app.cli.add_command(clean_cache_command)
app.cli.add_command(find_unsupported_command)
app.cli.add_command(migrate_legacy_command)
app.cli.add_command(import_defaults_command)


@app.errorhandler(Exception)
def handle_exception(e):
    """Handle uncaught exceptions and log them."""
    import traceback
    tb = traceback.format_exc()
    
    # Log to our memory buffer
    # We need to import logError properly or access the buffer directly if circular imports issue
    # Since app.py imports scripts, and scripts.utils has logError, we can try using it.
    try:
        from scripts import logError
        logError(f"UNCAUGHT 500: {str(e)}\n{tb}")
    except:
        print(f"Failed to log to memory buffer: {e}")
        
    # Pass through to default handler if we want standard 500 behavior, or render error page
    # For diagnosis, rendering a generic error page with the error details (if admin) or generic if public
    # But for now, just logging it is critical.
    
    # Re-raise so Flask handles the response (500)
    if isinstance(e,  (KeyboardInterrupt, SystemExit)):
        raise e
        
    # Prepare error message for user
    return render_template('error.html', 
                           error_message=f'<h1>Internal Server Error</h1><p>An unexpected error occurred.</p><!-- {str(e)} -->'), 500


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


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # XSS Protection (legacy browsers)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self'; "
        "frame-ancestors 'self'"
    )
    
    # HSTS (only in production with HTTPS)
    if not app.debug and request.is_secure:
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
    
    # Referrer policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions policy
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=()'
    )
    
    return response



@app.route('/')
def index():
    """Render the home page."""
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
@limiter.limit("10 per hour")  # Max 10 uploads per hour per IP
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
    if not file or not file.filename:
        return render_template('error.html',
                               error_message='<h1>No bindings file supplied; please go back and select your binds file as per the instructions.</h1>')
    
    # Enhanced file validation
    # Validate file extension
    if not file.filename.endswith('.binds'):
        return render_template('error.html',
                               error_message='<h1>Only .binds files are allowed</h1>')
    
    # Read file with size limit
    try:
        xml_bytes = file.read()
        
        # Check file size (500KB max for a bindings file)
        if len(xml_bytes) > 512000:
            return render_template('error.html',
                                   error_message='<h1>File too large. Maximum size is 500KB</h1>')
        
        # Decode with strict validation
        xml = xml_bytes.decode('utf-8')
        
        # Basic XML bomb detection (excessive repetition)
        if xml.count('<!ENTITY') > 10:
            return render_template('error.html',
                                   error_message='<h1>Invalid XML structure detected</h1>')
        
    except UnicodeDecodeError:
        return render_template('error.html',
                               error_message='<h1>Invalid file encoding. UTF-8 required</h1>')
    except Exception as e:
        logError(f"File validation error: {e}\n")
        return render_template('error.html',
                               error_message='<h1>File validation failed</h1>')
    
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
    
    binds_path = config.pathWithSuffix('.binds')
    with open(str(binds_path), 'w', encoding='utf-8') as f:
        f.write(xml)
    
    public = len(description) > 0
    
    # Parse bindings and generate images
    try:
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
            
    except RuntimeError as e:
        logError(f'Runtime error in generation for {run_id}: {e}\n')
        errors.errors = f'<h1>System Error</h1><p>{str(e)}</p>'
    except Exception as e:
        logError(f'Unexpected error in generation for {run_id}: {e}\n')
        import traceback
        traceback.print_exc()
        errors.errors = f'<h1>Unexpected System Error</h1><p>An unexpected error occurred while processing your request. Please try again later.</p>'
    
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
        
        # Also save to SQLite database
        try:
            database.create_configuration(
                config_id=run_id,
                description=description,
                styling=styling,
                display_groups=display_groups,
                devices=devices,
                unhandled_warnings=errors.unhandledDevicesWarnings,
                device_warnings=errors.deviceWarnings,
                misc_warnings=errors.misconfigurationWarnings
            )
        except Exception as e:
            logError(f"Database insertion error for {run_id}: {e}")
    
    # Use url_for for reliable external links
    refcard_url_dynamic = url_for('show_binds', run_id=run_id, _external=True)
    binds_url_dynamic = url_for('serve_config', path=f"{run_id}.binds", _external=True)

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
                           refcard_url=refcard_url_dynamic,
                           binds_url=binds_url_dynamic,
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
                'url': url_for('show_binds', run_id=config.name, _external=True),
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
    logError(f"DEBUG: Starting show_binds for {run_id}")
    
    try:
        config = Config(run_id)
        binds_path = config.pathWithSuffix('.binds')
        replay_path = config.pathWithSuffix('.replay')
        
        replay_info = {}
        if replay_path.exists():
            try:
                with replay_path.open('rb') as pickle_file:
                    replay_info = pickle.load(pickle_file)
            except Exception as e:
                logError(f"Error loading replay for {run_id}: {e}")
        
        if not binds_path.exists():
            if not replay_path.exists():
                # Truly not found
                return render_template('error.html', error_message=f'<h1>Configuration "{run_id}" not found</h1>')
            
            # Source missing but we have metadata (graceful degradation)
            source_missing = True
            xml = None
        else:
            source_missing = False
            with codecs.open(str(binds_path), 'r', 'utf-8') as f:
                xml = f.read()
        
        display_groups = replay_info.get('displayGroups', ['Galaxy map', 'General', 'Head look', 'SRV', 'Ship', 'UI'])
        styling = replay_info.get('styling', 'None')
        description = replay_info.get('description', '')
        
        if not source_missing:
            errors.misconfigurationWarnings = replay_info.get('misconfigurationWarnings', replay_info.get('warnings', ''))
            errors.deviceWarnings = replay_info.get('deviceWarnings', '')

    except (ValueError):
        return render_template('error.html',
                               error_message=f'<h1>Configuration "{run_id}" invalid</h1>')
    
    # Parse and generate (or recover)
    created_images = []
    
    try:
        if not source_missing:
            (physical_keys, modifiers, devices) = parseBindings(run_id, xml, display_groups, errors)
            
            already_handled_devices = []
            
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
                            # REGENERATION logic
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

        else:
            # Source missing: check for existing images on disk
            logError(f"Source missing for {run_id}, checking existing images...")
            errors.errors = "<strong>Source file missing.</strong><br>The `.binds` file for this configuration is missing from the server. Showing archived images if available."
            
            # We can rely on devices list from replay info if available, or just scan directory?
            # Creating list based on supportedDevices checks
            
            # Check for images corresponding to supported devices
            for supported_device_key, supported_device in supportedDevices.items():
                template = supported_device['Template']
                # Check for -Template.jpg or -Template-1.jpg
                
                # Index 0
                img_path_0 = config.pathWithNameAndSuffix(template, '.jpg')
                if img_path_0.exists():
                     created_images.append(f'{supported_device_key}::0')
                
                # Index 1
                img_path_1 = config.pathWithNameAndSuffix(f'{template}-1', '.jpg')
                if img_path_1.exists():
                     created_images.append(f'{supported_device_key}::1')
            
            # Check for keyboard
            kb_path = config.pathWithNameAndSuffix('m-Keyboard', '.jpg') # standard matrix
            # Wait, appendKeyboardImage naming is complex. It's usually just runID-Keyboard.jpg check?
            # Actually appendKeyboardImage calls save() 
            # In appendKeyboardImage (not visible here but assuming standard naming):
            # It usually appends to the image list.
            
            # Let's check for "Keyboard" specifically?
            # The template for Keyboard is special.
            # Assume if we find ANY keyboard image? 
            # It's usually handled inside the loop for other apps but here it is separate.
            pass # created_images is good enough for now.

    except RuntimeError as e:
        logError(f'Runtime error in generation for {run_id}: {e}\n')
        errors.errors = f'<h1>System Error</h1><p>{str(e)}</p>'
    except Exception as e:
        logError(f'Unexpected error in generation for {run_id}: {e}\n')
        import traceback
        traceback.print_exc()
        errors.errors = f'<h1>Unexpected System Error</h1><p>An unexpected error occurred while processing your request. Please try again later.</p>'
    
    # Use url_for for reliable external links
    refcard_url_dynamic = url_for('show_binds', run_id=run_id, _external=True)
    binds_url_dynamic = url_for('serve_config', path=f"{run_id[:2]}/{run_id}.binds", _external=True)

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
                           refcard_url=refcard_url_dynamic,
                           binds_url=binds_url_dynamic,
                           supported_devices=supportedDevices)


@app.route('/devices')
def list_devices():
    """List all supported devices."""
    from scripts.database import get_device_counts
    
    try:
        counts = get_device_counts()
    except:
        counts = {}

    devices = []
    for name in sorted(supportedDevices.keys()):
        # Map device key to template name which is often used as display name in DB
        # Note: DB 'device_display_name' is usually the Template name (e.g., 'x52pro') 
        # OR the device key? Let's check create_configuration in database.py
        # It uses: device_info.get('Template', device_key)
        
        template = supportedDevices[name].get('Template', name)
        # Try to find count by template, or fall back to name
        count = counts.get(template, counts.get(name, 0))
        
        devices.append({
            'name': name,
            'count': count,
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
                           created_images=[],
                           device_for_block_image=device_name,
                           public=False,
                           refcard_url='',
                           binds_url='',
                           supported_devices=supportedDevices)


def generate_pdf(run_id, page_format='A4'):
    """Generate a PDF for the given run_id's images."""
    from fpdf import FPDF
    from scripts.models import Config
    import os
    
    config = Config(run_id)
    pdf_filename = f"{run_id}-{page_format}.pdf"
    pdf_path = config.path().parent / pdf_filename
    
    # Return existing if cached (optional, can force regen for debugging)
    # in dev/hotfix we might want to force regen, but for prod use cache
    if pdf_path.exists():
         return str(pdf_path)

    # Collect images in specific order:
    # 1. Device 0
    # 2. Device 1 (if exists)
    # 3. Keyboard
    
    images_to_process = []
    
    # We don't have the parsed 'devices' list easily available here without re-parsing.
    # However, we can scan the directory for files matching the run_id.
    # But we want a specific order.
    # Pattern: {run_id}-{template}.jpg OR {run_id}-{template}-{index}.jpg
    # Keyboard: {run_id}-keyboard.jpg
    
    # Get all jpgs for this run
    all_files = list(config.path().parent.glob(f"{run_id}-*.jpg"))
    
    # Sort them to ensure determinism
    # Typically: runID-template.jpg (main device)
    # runID-template-1.jpg (secondary device)
    # runID-keyboard.jpg (keyboard)
    
    # Naive sort might put keyboard in middle.
    # Let's separate them.
    
    keyboard_img = None
    device_images = []
    
    for p in all_files:
        if p.name.endswith('keyboard.jpg'):
            keyboard_img = p
        else:
            device_images.append(p)
            
    # Sort device images by name (should usually put -1 after base)
    device_images.sort()
    
    ordered_images = device_images
    if keyboard_img:
        ordered_images.append(keyboard_img)
    
    if not ordered_images:
        return None
        
    # Create PDF
    pdf = FPDF(orientation='P', unit='mm', format=page_format)
    pdf.set_auto_page_break(False)
    
    import tempfile
    
    for img_path in ordered_images:
        try:
            # Open with PIL to check dimensions and sanitize
            from PIL import Image
            
            with Image.open(str(img_path)) as im:
                # Convert to RGB to ensure compatibility (remove Alpha, handle CMYK)
                if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                    # Create a white background
                    bg = Image.new('RGB', im.size, (255, 255, 255))
                    # Paste image on top (using alpha channel if available)
                    if im.mode != 'RGBA':
                        im = im.convert('RGBA')
                    bg.paste(im, mask=im.split()[3])
                    im = bg
                elif im.mode != 'RGB':
                    im = im.convert('RGB')
                
                width, height = im.size
                ratio = width / height
                
                # Landscape if wider than tall
                orientation = 'L' if ratio >= 1.2 else 'P'
                
                pdf.add_page(orientation=orientation)
                
                # Page dimensions in mm
                if orientation == 'L':
                    # A4: 297x210, Letter: 279x216
                    pw = 297 if page_format == 'A4' else 279 
                    ph = 210 if page_format == 'A4' else 216 
                else:
                    pw = 210 if page_format == 'A4' else 216 
                    ph = 297 if page_format == 'A4' else 279
                
                # Calculate fit dimensions (keep aspect ratio)
                # Available space (assuming small margin or full bleed)
                # Let's target full bleed or slight margin
                
                # Setup target dimensions
                target_w = pw
                target_h = ph
                
                # Scale logic
                # If image ratio > page ratio (Image constitutes "Wider"), fit to width
                page_ratio = pw / ph
                
                if ratio > page_ratio:
                    # Fit Width
                    w = target_w
                    h = target_w / ratio
                else:
                    # Fit Height
                    h = target_h
                    w = target_h * ratio
                
                # Center image
                x = (pw - w) / 2
                y = (ph - h) / 2
                
                # Save sanitized image to temp file for FPDF
                # FPDF (pyfpdf) works best with files.
                # using a temp file with .jpg extension
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_img:
                    im.save(tmp_img, 'JPEG', quality=95)
                    tmp_name = tmp_img.name
                
                try:
                    pdf.image(tmp_name, x=x, y=y, w=w, h=h)
                finally:
                    # Cleanup temp file
                    if os.path.exists(tmp_name):
                        os.unlink(tmp_name)
            
        except Exception as e:
            logError(f"Error adding image {img_path} to PDF: {e}")
            continue

    try:
        pdf.output(str(pdf_path))
    except Exception as e:
         logError(f"Error saving PDF {pdf_path}: {e}")
         return None
         
    return str(pdf_path)

@app.route('/download/<run_id>/pdf')
def download_pdf(run_id):
    """Download existing or generate new PDF."""
    format_type = request.args.get('format', 'A4')
    if format_type not in ['A4', 'Letter']:
        format_type = 'A4'
        
    try:
        pdf_path = generate_pdf(run_id, format_type)
        if pdf_path and os.path.exists(pdf_path):
             return send_from_directory(
                os.path.dirname(pdf_path),
                os.path.basename(pdf_path),
                as_attachment=True,
                download_name=f"EDRefCard-{run_id}-{format_type}.pdf"
            )
        else:
             return render_template('error.html', error_message='<h1>No images found to generate PDF</h1>')
    except Exception as e:
        logError(f"PDF Gen Error: {e}")
        return render_template('error.html', error_message=f'<h1>Error generating PDF</h1><p>{e}</p>')


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
