import sys
import os
from pathlib import Path

# Setup path to import from www
current_dir = Path(__file__).parent.resolve()
www_path = current_dir / 'www'
sys.path.insert(0, str(www_path))

try:
    print(f"sys.path: {sys.path}")
    import scripts
    print(f"scripts package: {scripts}")
    from scripts.parser import parseBindings
    from scripts.models import Config, Errors
    from scripts.bindingsData import supportedDevices
    from scripts.renderer import createHOTASImage, appendKeyboardImage
    print("Imports successful")
except Exception as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def reproduce():
    binds_file = current_dir / 'Schimz.4.2.binds'
    if not binds_file.exists():
        print(f"Error: {binds_file} not found")
        return

    print(f"Reading {binds_file}...")
    with open(binds_file, 'r', encoding='utf-8') as f:
        xml = f.read()

    run_id = 'test_debug'
    display_groups = ['Galaxy map', 'General', 'Head look', 'SRV', 'Ship', 'UI']
    errors = Errors()

    print("Parsing bindings...")
    try:
        (physical_keys, modifiers, devices) = parseBindings(run_id, xml, display_groups, errors)
        print("Parsing successful.")
        print(f"Devices found: {list(devices.keys())}")
        print(f"Errors: {errors.errors}")
    except Exception as e:
        print(f"CRASH during parsing: {e}")
        import traceback
        traceback.print_exc()
        return

    # Simulate image generation loop from app.py
    print("Simulating image generation...")
    config = Config.newRandom() # Mock config
    config.setDirRoot(current_dir / 'www') # Mock root
    
    # We need to mock Config to avoid actual file system writes if possible, 
    # but createHOTASImage likely writes files.
    # For reproduction, we might want to just see if it crashes.
    
    already_handled_devices = []
    created_images = []
    
    try:
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
                        print(f"Generating image for {supported_device_key}...")
                        createHOTASImage(
                            physical_keys, modifiers, 
                            supported_device['Template'], 
                            supported_device['HandledDevices'], 
                            40, config, True, 'None', device_index, 
                            errors.misconfigurationWarnings
                        )
                        created_images.append(f'{supported_device_key}::{device_index}')
                        for handled_device in supported_device['HandledDevices']:
                            already_handled_devices.append(f'{handled_device}::{device_index}')
                            
        if devices.get('Keyboard::0') is not None:
             print("Generating Keyboard image...")
             appendKeyboardImage(created_images, physical_keys, modifiers, display_groups, run_id, True)

        print("Generation finished successfully.")

    except Exception as e:
        print(f"CRASH during image generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
