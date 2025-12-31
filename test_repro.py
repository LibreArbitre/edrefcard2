
import sys
import os
from pathlib import Path
import unittest

# Mimic test_bindings.py setup
current_dir = Path(__file__).parent.resolve()
scripts_path = current_dir / 'www' / 'scripts'
sys.path.insert(0, str(scripts_path.parent)) # Add www to path to allow www.scripts import ?? relative?
# Actually test_bindings adds "www.scripts" by being in root and assumes root is in path.
# But it does os.chdir.

# Let's try to import wand directly first to see if it works here
try:
    import wand
    from wand.drawing import Drawing
    print(f"Wand imported successfully: {wand}")
except ImportError as e:
    print(f"FAILED to import wand: {e}")

# Setup environment for imports from www/scripts
sys.path.insert(0, str(current_dir / 'www'))

try:
    from scripts import renderer
    print(f"Renderer imported. Drawing is: {renderer.Drawing}")
    from scripts import parser
except ImportError as e:
    print(f"Failed to import scripts modules: {e}")

class TestRepro(unittest.TestCase):
    def test_parse_schimz(self):
        print("\nTesting Schimz.4.2.binds parsing...")
        binds_file = current_dir / 'Schimz.4.2.binds'
        if not binds_file.exists():
            self.fail(f"{binds_file} not found")
        
        with open(binds_file, 'r', encoding='utf-8') as f:
            xml = f.read()
            
        from scripts.models import Config, Errors
        from scripts.parser import parseBindings
        
        errors = Errors()
        display_groups = ['Galaxy map', 'General', 'Head look', 'SRV', 'Ship', 'UI']
        run_id = 'test_repro'
        
        try:
            (physical_keys, modifiers, devices) = parseBindings(run_id, xml, display_groups, errors)
            print("Parsing SUCCESS")
            print(f"Devices: {list(devices.keys())}")
            
            # Test Error Handling for Missing Library
            print("Verifying RuntimeError when wand is missing...")
            try:
                from scripts.renderer import createHOTASImage
            except ImportError:
                # If we can't import it because of top level errors, that's an issue, 
                # but renderer seems to import fine now even without wand.
                pass

            original_drawing = renderer.Drawing
            renderer.Drawing = None
            try:
                # Mock config and data for call
                from scripts.models import Config
                config = Config.newRandom()
                config.setDirRoot(current_dir / 'www')
                
                # Use first device found
                if devices:
                    dev_key = list(devices.keys())[0]
                    dev_info = devices[dev_key]
                    if dev_info:
                        template = dev_info['Template']
                        handled = dev_info['HandledDevices']
                        idx = int(dev_key.split('::')[1]) if '::' in dev_key else 0
                        
                        with self.assertRaises(RuntimeError) as cm:
                            createHOTASImage(
                                physical_keys, modifiers, 
                                template, 
                                handled, 
                                40, config, True, 'None', idx, 
                                errors.misconfigurationWarnings
                            )
                        print(f"Caught expected RuntimeError: {cm.exception}")
            finally:
                renderer.Drawing = original_drawing

        except Exception as e:
            print(f"CRASH: {e}")
            import traceback
            traceback.print_exc()
            self.fail(f"Crash: {e}")
                
        except Exception as e:
            print(f"CRASH: {e}")
            import traceback
            traceback.print_exc()
            self.fail(f"Crash: {e}")

if __name__ == '__main__':
    # Fix cwd for renderer relative file operations
    os.chdir(current_dir / 'www/scripts')
    unittest.main()
