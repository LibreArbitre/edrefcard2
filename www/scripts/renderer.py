#!/usr/bin/env python3
"""
EDRefCard Renderer Module

This module contains functions for generating reference card images
using the Wand/ImageMagick library.
"""

import re
from pathlib import Path
from collections import OrderedDict

try:
    from wand.drawing import Drawing
    from wand.image import Image
    from wand.font import Font
    from wand.color import Color
except ImportError as e:
    # Log the error but don't fail immediately to allow app to start
    print(f"Warning: Failed to import wand (ImageMagick): {e}")
    Drawing = None
    Image = None
    Font = None
    Color = None

from .models import Config
from .utils import getFontPath, transKey, logError

# Import data files
try:
    from .bindingsData import supportedDevices, hotasDetails
except ImportError:  # pragma: no cover
    from bindingsData import supportedDevices, hotasDetails

# Import styles (lazy to avoid circular imports)
_styles_initialized = False
groupStyles = None
categoryStyles = None
ModifierStyles = None


def _init_styles():
    """Lazily initialize styles to avoid circular imports."""
    global _styles_initialized, groupStyles, categoryStyles, ModifierStyles
    if not _styles_initialized:
        try:
            from .styles import groupStyles as gs, categoryStyles as cs, ModifierStyles as ms
        except ImportError:
            from styles import groupStyles as gs, categoryStyles as cs, ModifierStyles as ms
        groupStyles = gs
        categoryStyles = cs
        ModifierStyles = ms
        _styles_initialized = True


def writeUrlToDrawing(config, drawing, public):
    """Write the reference card URL to the image.
    
    Args:
        config: Config object
        drawing: Wand Drawing context
        public: Whether this is a public reference card
    """
    url = config.refcardURL() if public else Config.webRoot()
    drawing.push()
    drawing.font = getFontPath('SemiBold', 'Normal')
    drawing.font_size = 36
    drawing.text(x=23, y=252, body=url)
    drawing.pop()


def createKeyboardImage(physicalKeys, modifiers, source, imageDevices, 
                        biggestFontSize, displayGroups, runId, public):
    """Create a keyboard reference card image.
    
    Args:
        physicalKeys: Dictionary of physical key bindings
        modifiers: Dictionary of modifier key bindings
        source: Template image name
        imageDevices: List of device names to include
        biggestFontSize: Maximum font size to use
        displayGroups: List of control groups to display
        runId: Configuration run identifier
        public: Whether this is a public configuration
    
    Returns:
        True if image was created successfully
    """
    if Drawing is None:
        raise RuntimeError("Image generation library (ImageMagick/Wand) is not installed or failed to load.")
        
    _init_styles()
    config = Config(runId)
    filePath = config.pathWithNameAndSuffix(source, '.jpg')

    # Check if already exists
    if filePath.exists():
        return True
    
    with Image(filename='../res/' + source + '.jpg') as sourceImg:
        with Drawing() as context:
            # Font defaults
            context.font = getFontPath('Regular', 'Normal')
            context.text_antialias = True
            context.font_style = 'normal'
            context.stroke_width = 1
            context.fill_opacity = 1
            context.fill_color = Color('Black')

            # Add URL to title
            writeUrlToDrawing(config, context, public)

            # Organize outputs by group
            outputs = {group: {} for group in displayGroups}

            # Find bindings and order them
            for _physicalKeySpec, physicalKey in physicalKeys.items():
                itemDevice = physicalKey.get('Device')
                itemKey = physicalKey.get('Key')

                if itemDevice not in imageDevices:
                    continue

                for modifier, bind in physicalKey.get('Binds').items():
                    for _controlKey, control in bind.get('Controls').items():
                        bindInfo = {
                            'Control': control,
                            'Key': itemKey,
                            'Modifiers': []
                        }

                        if modifier != 'Unmodified':
                            for _modifierKey, modifierControls in modifiers.items():
                                for modifierControl in modifierControls:
                                    if (modifierControl.get('ModifierKey') == modifier 
                                            and modifierControl.get('Key') is not None):
                                        bindInfo['Modifiers'].append(modifierControl.get('Key'))

                        outputs[control['Group']][control['Name']] = bindInfo

            # Set up screen state for layout
            screenState = {
                'baseX': 60,
                'baseY': 320,
                'maxWidth': 0,
                'thisWidth': 0,
                'currentX': 60,
                'currentY': 320,
            }

            font = Font(getFontPath('Regular', 'Normal'), antialias=True, size=biggestFontSize)
            groupTitleFont = Font(getFontPath('Regular', 'Normal'), antialias=True, size=biggestFontSize * 2)
            context.stroke_width = 1
            context.stroke_color = Color('Black')
            context.fill_opacity = 0

            # Render each display group
            for displayGroup in displayGroups:
                if not outputs[displayGroup]:
                    continue

                writeText(context, sourceImg, displayGroup, screenState, groupTitleFont, False, True)

                orderedOutputs = OrderedDict(
                    sorted(outputs[displayGroup].items(), 
                           key=lambda x: x[1].get('Control').get('Order'))
                )
                for _bindKey, bind in orderedOutputs.items():
                    for modifier in bind.get('Modifiers', []):
                        writeText(context, sourceImg, transKey(modifier), screenState, font, True, False)
                    writeText(context, sourceImg, transKey(bind.get('Key')), screenState, font, True, False)
                    writeText(context, sourceImg, bind.get('Control').get('Name'), screenState, font, False, True)

            context.draw(sourceImg)
            sourceImg.save(filename=str(filePath))
    
    return True


def appendKeyboardImage(createdImages, physicalKeys, modifiers, displayGroups, runId, public):
    """Create and append a keyboard image to the list of created images.
    
    Args:
        createdImages: List to append created image name to
        physicalKeys: Dictionary of physical key bindings
        modifiers: Dictionary of modifier bindings
        displayGroups: List of control groups to display
        runId: Configuration run identifier
        public: Whether this is a public configuration
    """
    def countKeyboardItems(physicalKeys):
        keyboardItems = 0
        for physicalKey in physicalKeys.values():
            if physicalKey.get('Device') == 'Keyboard':
                for bind in physicalKey.get('Binds').values():
                    keyboardItems += len(bind.get('Controls'))
        return keyboardItems
    
    def fontSizeForKeyBoardItems(physicalKeys):
        keyboardItems = countKeyboardItems(physicalKeys)
        if keyboardItems > 48:
            fontSize = 40 - int(((keyboardItems - 48) / 20) * 4)
            if fontSize < 24:
                fontSize = 24
        else:
            fontSize = 40
        return fontSize
    
    fontSize = fontSizeForKeyBoardItems(physicalKeys)
    createKeyboardImage(physicalKeys, modifiers, 'keyboard', ['Keyboard'], 
                        fontSize, displayGroups, runId, public)
    createdImages.append('Keyboard')


def createKeyboardLayoutImage(physicalKeys, layout, config, styling):
    """Create a visual keyboard layout image with bindings overlaid on keys.

    Overlays key bindings onto a keyboard image (keyboard-layout.jpg).
    Currently only ANSI 104-key is implemented; ISO/Cyrillic fall through
    to return None (caller should fall back to text list).

    Args:
        physicalKeys: Dictionary of physical key bindings
        layout: 'ansi', 'iso', or 'cyrillic'
        config: Config object (for output file path)
        styling: Styling mode ('None', 'Group', 'Category', 'Modifier')

    Returns:
        True if image was created, None if layout not supported
    """
    if Drawing is None:
        raise RuntimeError("Image generation library (ImageMagick/Wand) is not installed.")

    # Only ANSI is implemented in this simplified version
    if layout != 'ansi':
        return None

    _init_styles()

    try:
        from .keyboardLayouts import keyboardLayouts
    except ImportError:
        from keyboardLayouts import keyboardLayouts

    layoutMapping = keyboardLayouts.get('ANSI 104', {})

    filePath = config.pathWithNameAndSuffix('keyboard-layout', '.jpg')
    if filePath.exists():
        return True

    # The keyboard-layout.jpg is in www/static/images/; renderer runs from www/
    sourceImagePath = Path('../www/static/images/keyboard-layout.jpg')
    if not sourceImagePath.exists():
        # Try alternate relative paths depending on working directory
        for candidate in [
            Path('static/images/keyboard-layout.jpg'),
            Path('../static/images/keyboard-layout.jpg'),
            Path('/app/www/static/images/keyboard-layout.jpg'),
        ]:
            if candidate.exists():
                sourceImagePath = candidate
                break
        else:
            return None  # Image not found, skip silently

    with Image(filename=str(sourceImagePath)) as sourceImg:
        imgWidth = sourceImg.width
        imgHeight = sourceImg.height

        with Drawing() as context:
            context.text_antialias = True
            context.font = getFontPath('Regular', 'Normal')
            context.font_size = 28
            context.stroke_width = 0
            context.fill_opacity = 1

            # Add URL watermark at bottom
            context.push()
            context.font = getFontPath('SemiBold', 'Normal')
            context.font_size = 36
            context.fill_color = Color('Black')
            context.text(x=23, y=imgHeight - 20, body=config.refcardURL())
            context.pop()

            # Collect one representative binding per key
            keyBindings = {}  # keyName -> list of (controlName, style)
            for _physicalKeySpec, physicalKey in physicalKeys.items():
                if physicalKey.get('Device') != 'Keyboard':
                    continue

                keyName = physicalKey.get('Key')
                displayLabel = layoutMapping.get(keyName)
                if not displayLabel:
                    continue  # Key not in ANSI mapping

                if keyName not in keyBindings:
                    keyBindings[keyName] = []

                for _modifier, bind in physicalKey.get('Binds', {}).items():
                    for _controlKey, control in bind.get('Controls', {}).items():
                        if styling == 'Group':
                            style = groupStyles.get(control.get('Group'), groupStyles.get('General'))
                        elif styling == 'Category':
                            style = categoryStyles.get(control.get('Category', 'General'), categoryStyles.get('General'))
                        elif styling == 'Modifier':
                            style = ModifierStyles.index(0)
                        else:
                            style = groupStyles.get('General')
                        keyBindings[keyName].append({
                            'name': control.get('Name', ''),
                            'style': style,
                        })

            # Lay out text annotations on a grid matching the keyboard image.
            # The keyboard-layout.jpg image has a standard ANSI layout.
            # We use a calculated grid based on the image dimensions.
            # Row y-positions and per-row key x-positions (as fraction of imgWidth).
            # These approximate the standard ANSI keyboard photo layout.
            keyPositions = _ansiKeyPositions(imgWidth, imgHeight)

            for keyName, binds in keyBindings.items():
                if not binds:
                    continue
                pos = keyPositions.get(keyName)
                if not pos:
                    continue

                x, y = pos
                # Clip to at most 2 bindings per key to avoid overlap
                for i, bindInfo in enumerate(binds[:2]):
                    name = bindInfo['name']
                    style = bindInfo['style']
                    # Shorten long names
                    if len(name) > 12:
                        name = name[:11] + '…'
                    context.fill_color = style['Color']
                    context.font = style['Font']
                    context.font_size = 22
                    context.text(x=x, y=y + i * 26, body=name)

            context.draw(sourceImg)
            sourceImg.save(filename=str(filePath))

    return True


def _ansiKeyPositions(imgWidth, imgHeight):
    """Return approximate pixel positions for each ANSI key in keyboard-layout.jpg.

    Coordinates are the top-left corner of the text annotation area for each key.
    These are calculated as fractions of the image dimensions so they scale
    with different image sizes.

    Returns:
        Dict mapping Elite Dangerous key name -> (x, y) pixel position
    """
    # keyboard-layout.jpg is a standard ANSI keyboard photo.
    # Approximate row y-positions as fractions of image height:
    w, h = imgWidth, imgHeight

    # Row top y-positions (fraction of height)
    rFn  = 0.04   # Function key row
    rNum = 0.19   # Number row
    rTab = 0.35   # Tab row (QWERTY)
    rCap = 0.51   # Caps Lock row (ASDF)
    rSft = 0.66   # Shift row (ZXCV)
    rBot = 0.82   # Bottom row (Space etc.)
    rNav = 0.19   # Nav cluster (same height as number row)
    rNum2= 0.19   # Numpad top

    def p(xf, yf):
        return (int(xf * w), int(yf * h))

    return {
        # --- Function keys ---
        'Key_Escape':      p(0.005, rFn),
        'Key_F1':          p(0.073, rFn),
        'Key_F2':          p(0.110, rFn),
        'Key_F3':          p(0.147, rFn),
        'Key_F4':          p(0.183, rFn),
        'Key_F5':          p(0.228, rFn),
        'Key_F6':          p(0.265, rFn),
        'Key_F7':          p(0.302, rFn),
        'Key_F8':          p(0.338, rFn),
        'Key_F9':          p(0.383, rFn),
        'Key_F10':         p(0.420, rFn),
        'Key_F11':         p(0.457, rFn),
        'Key_F12':         p(0.493, rFn),
        # --- Number row ---
        'Key_Grave':       p(0.005, rNum),
        'Key_1':           p(0.042, rNum),
        'Key_2':           p(0.079, rNum),
        'Key_3':           p(0.116, rNum),
        'Key_4':           p(0.153, rNum),
        'Key_5':           p(0.190, rNum),
        'Key_6':           p(0.227, rNum),
        'Key_7':           p(0.264, rNum),
        'Key_8':           p(0.301, rNum),
        'Key_9':           p(0.338, rNum),
        'Key_0':           p(0.375, rNum),
        'Key_Minus':       p(0.412, rNum),
        'Key_Equals':      p(0.449, rNum),
        'Key_Backspace':   p(0.468, rNum),
        # --- Tab row ---
        'Key_Tab':         p(0.005, rTab),
        'Key_Q':           p(0.057, rTab),
        'Key_W':           p(0.094, rTab),
        'Key_E':           p(0.131, rTab),
        'Key_R':           p(0.168, rTab),
        'Key_T':           p(0.205, rTab),
        'Key_Y':           p(0.242, rTab),
        'Key_U':           p(0.279, rTab),
        'Key_I':           p(0.316, rTab),
        'Key_O':           p(0.353, rTab),
        'Key_P':           p(0.390, rTab),
        'Key_LeftBracket': p(0.427, rTab),
        'Key_RightBracket':p(0.464, rTab),
        'Key_BackSlash':   p(0.486, rTab),
        # --- Caps row ---
        'Key_CapsLock':    p(0.005, rCap),
        'Key_A':           p(0.064, rCap),
        'Key_S':           p(0.101, rCap),
        'Key_D':           p(0.138, rCap),
        'Key_F':           p(0.175, rCap),
        'Key_G':           p(0.212, rCap),
        'Key_H':           p(0.249, rCap),
        'Key_J':           p(0.286, rCap),
        'Key_K':           p(0.323, rCap),
        'Key_L':           p(0.360, rCap),
        'Key_SemiColon':   p(0.397, rCap),
        'Key_Apostrophe':  p(0.434, rCap),
        'Key_Enter':       p(0.456, rCap),
        # --- Shift row ---
        'Key_LeftShift':   p(0.005, rSft),
        'Key_Z':           p(0.079, rSft),
        'Key_X':           p(0.116, rSft),
        'Key_C':           p(0.153, rSft),
        'Key_V':           p(0.190, rSft),
        'Key_B':           p(0.227, rSft),
        'Key_N':           p(0.264, rSft),
        'Key_M':           p(0.301, rSft),
        'Key_Comma':       p(0.338, rSft),
        'Key_Period':      p(0.375, rSft),
        'Key_Slash':       p(0.412, rSft),
        'Key_RightShift':  p(0.438, rSft),
        # --- Bottom row ---
        'Key_LeftControl': p(0.005, rBot),
        'Key_LeftWindows': p(0.057, rBot),
        'Key_LeftAlt':     p(0.094, rBot),
        'Key_Space':       p(0.185, rBot),
        'Key_RightAlt':    p(0.360, rBot),
        'Key_RightWindows':p(0.397, rBot),
        'Key_Application': p(0.430, rBot),
        'Key_RightControl':p(0.460, rBot),
        # --- Navigation cluster ---
        'Key_PrintScreen': p(0.545, rNav),
        'Key_ScrollLock':  p(0.582, rNav),
        'Key_Pause':       p(0.619, rNav),
        'Key_Insert':      p(0.545, 0.35),
        'Key_Home':        p(0.582, 0.35),
        'Key_PageUp':      p(0.619, 0.35),
        'Key_Delete':      p(0.545, 0.51),
        'Key_End':         p(0.582, 0.51),
        'Key_PageDown':    p(0.619, 0.51),
        # --- Arrow keys ---
        'Key_UpArrow':     p(0.582, 0.74),
        'Key_LeftArrow':   p(0.545, 0.82),
        'Key_DownArrow':   p(0.582, 0.82),
        'Key_RightArrow':  p(0.619, 0.82),
        # --- Numpad ---
        'Key_NumLock':     p(0.660, rNum2),
        'Key_Numpad_Divide':   p(0.697, rNum2),
        'Key_Numpad_Multiply': p(0.734, rNum2),
        'Key_Numpad_Subtract': p(0.771, rNum2),
        'Key_Numpad_7':    p(0.660, 0.35),
        'Key_Numpad_8':    p(0.697, 0.35),
        'Key_Numpad_9':    p(0.734, 0.35),
        'Key_Numpad_Add':  p(0.771, 0.35),
        'Key_Numpad_4':    p(0.660, 0.51),
        'Key_Numpad_5':    p(0.697, 0.51),
        'Key_Numpad_6':    p(0.734, 0.51),
        'Key_Numpad_1':    p(0.660, 0.66),
        'Key_Numpad_2':    p(0.697, 0.66),
        'Key_Numpad_3':    p(0.734, 0.66),
        'Key_Numpad_Enter':p(0.771, 0.66),
        'Key_Numpad_0':    p(0.660, 0.82),
        'Key_Numpad_Decimal': p(0.734, 0.82),
    }


def writeText(context, img, text, screenState, font, surround, newLine):
    """Write text to an image with wrapping support.
    
    Args:
        context: Wand Drawing context
        img: Wand Image
        text: Text to write
        screenState: Dictionary tracking current position
        font: Font to use
        surround: Whether to draw a box around the text
        newLine: Whether to move to next line after writing
    """
    border = 4

    context.font = font.path
    context.font_style = 'normal'
    context.font_size = font.size
    
    context.push()
    
    context.stroke_width = 0
    context.fill_opacity = 1 
    context.fill_color = Color('Black')

    if text is None or text == '':
        context.fill_color = Color('Red')
        text = 'invalid'

    metrics = context.get_font_metrics(img, text, multiline=False)
    
    # Check if we need to wrap to next column
    if screenState['currentY'] + int(metrics.text_height + 32) > 2160:
        screenState['currentY'] = screenState['baseY']
        screenState['baseX'] = screenState['baseX'] + screenState['maxWidth'] + 49
        screenState['currentX'] = screenState['baseX']
        screenState['maxWidth'] = 0
        screenState['thisWidth'] = 0
    
    x = screenState['currentX']
    y = screenState['currentY'] + int(metrics.ascender)
    context.text(x=x, y=y, body=text)
    context.pop()

    if surround:
        y = screenState['currentY'] - border
        context.rectangle(
            left=x - (border * 4), 
            top=y - (border * 2), 
            width=int(metrics.text_width) + (border * 8), 
            height=int(metrics.text_height) + (border * 4), 
            radius=30
        )
        width = int(metrics.text_width + 48)
    else:
        width = int((metrics.text_width + 72) / 48) * 48
    
    screenState['thisWidth'] += width

    if newLine:
        if screenState['thisWidth'] > screenState['maxWidth']:
            screenState['maxWidth'] = screenState['thisWidth']
        screenState['currentY'] += int(metrics.text_height + 32)
        screenState['currentX'] = screenState['baseX']
        screenState['thisWidth'] = 0
    else:
        screenState['currentX'] += width


def createBlockImage(supportedDeviceKey, strokeColor='Red', fillColor='LightGreen', dryRun=False):
    """Create a block diagram image showing all controls on a device.
    
    Args:
        supportedDeviceKey: Name of the supported device
        strokeColor: Color for control box borders
        fillColor: Color for control box fills
        dryRun: If True, don't actually save the image
    
    Raises:
        KeyError: If device is not supported
    """
    if Drawing is None and not dryRun:
        raise RuntimeError("Image generation library (ImageMagick/Wand) is not installed or failed to load.")
        
    _init_styles()
    supportedDevice = supportedDevices[supportedDeviceKey]
    templateName = supportedDevice['Template']
    config = Config(templateName)
    config.makeDir()
    filePath = config.pathWithSuffix('.jpg')
    
    with Image(filename='../res/' + supportedDevice['Template'] + '.jpg') as sourceImg:
        with Drawing() as context:
            if not dryRun:        
                context.font = getFontPath('Regular', 'Normal')
                context.text_antialias = True
                context.font_style = 'normal'
            maxFontSize = 40

            for keyDevice in supportedDevice.get('KeyDevices', supportedDevice.get('HandledDevices')):
                for (keycode, box) in hotasDetails[keyDevice].items():
                    if keycode == 'displayName':
                        continue
                    if not dryRun:        
                        context.stroke_width = 1
                        context.stroke_color = Color(strokeColor)
                        context.fill_color = Color(fillColor)
                        context.rectangle(
                            top=box['y'], 
                            left=box['x'], 
                            width=box['width'], 
                            height=box.get('height', 54)
                        )
                        context.stroke_width = 0
                        context.fill_color = Color('Black')
                        sourceTexts = [{
                            'Text': keycode, 
                            'Group': 'General', 
                            'Style': groupStyles['General']
                        }]
                        texts = layoutText(sourceImg, context, sourceTexts, box, maxFontSize)
                        for text in texts:
                            context.font_size = text['Size']
                            context.font = text['Style']['Font']
                            context.text(x=text['X'], y=text['Y'], body=text['Text'])
            
            if not dryRun:        
                context.draw(sourceImg)
                sourceImg.save(filename=str(filePath))


def isRedundantSpecialisation(control, bind):
    """Check if a binding is a redundant specialisation.
    
    Args:
        control: Control dictionary with 'HideIfSameAs' list
        bind: Bind dictionary with 'Controls' ordered dict
    
    Returns:
        True if this is a redundant specialisation
    """
    moreGeneralControls = control.get('HideIfSameAs', [])
    if len(moreGeneralControls) == 0:
        return False
    
    for moreGeneralMatch in bind.get('Controls').keys():
        if moreGeneralMatch in moreGeneralControls:
            return True
    
    return False


def createHOTASImage(physicalKeys, modifiers, source, imageDevices, biggestFontSize, 
                     config, public, styling, deviceIndex, misconfigurationWarnings):
    """Create a HOTAS reference card image.
    
    Args:
        physicalKeys: Dictionary of physical key bindings
        modifiers: Dictionary of modifier bindings
        source: Template image name
        imageDevices: List of device names to include
        biggestFontSize: Maximum font size
        config: Config object
        public: Whether this is public
        styling: Styling mode ('None', 'Group', 'Category', 'Modifier')
        deviceIndex: Device index (0 or 1)
```
        misconfigurationWarnings: Current misconfiguration warnings string
    
    Returns:
        True if image was created successfully
    """
    if Drawing is None:
        raise RuntimeError("Image generation library (ImageMagick/Wand) is not installed or failed to load.")

    _init_styles()

    runId = config.name
    
    if deviceIndex == 0:
        name = source
    else:
        name = '%s-%s' % (source, deviceIndex)
    filePath = config.pathWithNameAndSuffix(name, '.jpg')
    
    # Check if already exists
    if filePath.exists():
        return True
    
    # Ensure template exists
    from pathlib import Path
    template_path = Path('../res') / (source + '.jpg')
    if not template_path.exists():
        raise FileNotFoundError(f"Template image '../res/{source}.jpg' not found")

    with Image(filename=str(template_path)) as sourceImg:

        with Drawing() as context:
            # Font defaults
            context.font = getFontPath('Regular', 'Normal')
            context.text_antialias = True
            context.font_style = 'normal'
            context.stroke_width = 0
            context.fill_color = Color('Black')
            context.fill_opacity = 1

            # Add URL to title
            writeUrlToDrawing(config, context, public)

            for physicalKeySpec, physicalKey in physicalKeys.items():
                itemDevice = physicalKey.get('Device')
                itemDeviceIndex = int(physicalKey.get('DeviceIndex'))
                itemDeviceKey = f'{itemDevice}::{itemDeviceIndex}'
                itemKey = physicalKey.get('Key')

                # Only show for appropriate device
                if itemDevice not in imageDevices and itemDeviceKey not in imageDevices:
                    continue

                # Only show for appropriate index
                if itemDeviceIndex != deviceIndex: 
                    continue

                # Find control details
                texts = []
                hotasDetail = None
                try:
                    if itemDeviceKey in hotasDetails:
                        hotasDetail = hotasDetails.get(itemDeviceKey).get(itemKey)
                    else:
                        hotasDetail = hotasDetails.get(itemDevice).get(itemKey)
                except AttributeError:
                    hotasDetail = None
                
                if hotasDetail is None:
                    logError('%s: No drawing box found for %s\n' % (runId, physicalKeySpec))
                    continue

                # Get modifiers
                for keyModifier in modifiers.get(physicalKeySpec, []):
                    if styling == 'Modifier':
                        style = ModifierStyles.index(keyModifier.get('Number'))
                    else:
                        style = groupStyles.get('Modifier')
                    texts.append({
                        'Text': 'Modifier %s' % keyModifier.get('Number'), 
                        'Group': 'Modifier', 
                        'Style': style
                    })
                
                # Handle positive/negative modifiers for joystick axes
                if '::Joy' in physicalKeySpec:
                    for variant in ['::Pos_Joy', '::Neg_Joy']:
                        for keyModifier in modifiers.get(physicalKeySpec.replace('::Joy', variant), []):
                            if styling == 'Modifier':
                                style = ModifierStyles.index(keyModifier.get('Number'))
                            else:
                                style = groupStyles.get('Modifier')
                            texts.append({
                                'Text': 'Modifier %s' % keyModifier.get('Number'), 
                                'Group': 'Modifier', 
                                'Style': style
                            })

                # Get unmodified bindings
                for modifier, bind in physicalKey.get('Binds').items():
                    if modifier == 'Unmodified':
                        for _controlKey, control in bind.get('Controls').items():
                            if isRedundantSpecialisation(control, bind):
                                continue
                            
                            # Check for misconfigured analogue controls
                            if (control.get('Type') == 'Digital' 
                                    and control.get('HasAnalogue') is True 
                                    and hotasDetail.get('Type') == 'Analogue'):
                                if misconfigurationWarnings == '':
                                    misconfigurationWarnings = (
                                        '<h1>Misconfiguration detected</h1>'
                                        'You have one or more analogue controls configured incorrectly. '
                                        'Please see <a href="https://forums.frontier.co.uk/threads/627609/">'
                                        'this thread</a> for details of the problem and how to correct it.<br/> '
                                        '<b>Your misconfigured controls:</b> <b>%s</b> ' % control['Name']
                                    )
                                else:
                                    misconfigurationWarnings = '%s, <b>%s</b>' % (
                                        misconfigurationWarnings, control['Name']
                                    )

                            # Determine style
                            if styling == 'Modifier':
                                style = ModifierStyles.index(0)
                            elif styling == 'Category':
                                style = categoryStyles.get(control.get('Category', 'General'))
                            else:
                                style = groupStyles.get(control.get('Group'))
                            
                            texts.append({
                                'Text': control.get('Name'),
                                'Group': control.get('Group'),
                                'Style': style
                            })

                # Get modified bindings
                for curModifierNum in range(1, 200):
                    for modifier, bind in physicalKey.get('Binds').items():
                        if modifier != 'Unmodified':
                            keyModifiers = modifiers.get(modifier)
                            modifierNum = 0
                            for keyModifier in keyModifiers:
                                if keyModifier['ModifierKey'] == modifier:
                                    modifierNum = keyModifier['Number']
                                    break
                            
                            if modifierNum != curModifierNum:
                                continue
                            
                            for _controlKey, control in bind.get('Controls').items():
                                if isRedundantSpecialisation(control, bind):
                                    continue
                                
                                if styling == 'Modifier':
                                    style = ModifierStyles.index(curModifierNum)
                                    texts.append({
                                        'Text': control.get('Name'),
                                        'Group': 'Modifier',
                                        'Style': style
                                    })
                                elif styling == 'Category':
                                    style = categoryStyles.get(control.get('Category', 'General'))
                                    texts.append({
                                        'Text': '%s[%s]' % (control.get('Name'), curModifierNum),
                                        'Group': control.get('Group'),
                                        'Style': style
                                    })
                                else:
                                    style = groupStyles.get(control.get('Group'))
                                    texts.append({
                                        'Text': '%s[%s]' % (control.get('Name'), curModifierNum),
                                        'Group': control.get('Group'),
                                        'Style': style
                                    })

                # Layout and render texts
                texts = layoutText(sourceImg, context, texts, hotasDetail, biggestFontSize)
                for text in texts:
                    context.font_size = text['Size']
                    context.font = text['Style']['Font']
                    if styling != 'None':
                        context.fill_color = text['Style']['Color']
                    context.text(x=text['X'], y=text['Y'], body=text['Text'])

            # Add standalone modifiers
            for modifierSpec, keyModifiers in modifiers.items():
                modifierTexts = []
                for keyModifier in keyModifiers:
                    if keyModifier.get('Device') not in imageDevices:
                        continue
                    if int(keyModifier.get('DeviceIndex')) != deviceIndex:
                        continue
                    if '/' in modifierSpec:
                        continue
                    
                    # Check if already handled
                    variants = [modifierSpec]
                    if '::Joy' in modifierSpec:
                        variants.extend([
                            modifierSpec.replace('::Pos_Joy', '::Joy'),
                            modifierSpec.replace('::Neg_Joy', '::Joy')
                        ])
                    if any(physicalKeys.get(v) is not None for v in variants):
                        continue

                    modifierKey = keyModifier.get('Key')
                    hotasDetail = hotasDetails.get(keyModifier.get('Device')).get(modifierKey)
                    if hotasDetail is None:
                        logError('%s: No location for %s\n' % (runId, modifierSpec))
                        continue

                    if styling == 'Modifier':
                        style = ModifierStyles.index(keyModifier.get('Number'))
                    else:
                        style = groupStyles.get('Modifier')
                    modifierTexts.append({
                        'Text': 'Modifier %s' % keyModifier.get('Number'),
                        'Group': 'Modifier',
                        'Style': style
                    })

                if modifierTexts:
                    modifierTexts = layoutText(sourceImg, context, modifierTexts, hotasDetail, biggestFontSize)
                    for text in modifierTexts:
                        context.font_size = text['Size']
                        context.font = text['Style']['Font']
                        if styling != 'None':
                            context.fill_color = text['Style']['Color']
                        context.text(x=text['X'], y=text['Y'], body=text['Text'])

            context.draw(sourceImg)
            sourceImg.save(filename=str(filePath))
    
    return True


def layoutText(img, context, texts, hotasDetail, biggestFontSize):
    """Calculate text layout within a bounding box.
    
    Args:
        img: Wand Image for font metrics
        context: Drawing context
        texts: List of text dictionaries
        hotasDetail: Bounding box info (x, y, width, height)
        biggestFontSize: Maximum font size
    
    Returns:
        List of texts with X, Y, Size added
    """
    width = hotasDetail.get('width')
    height = hotasDetail.get('height', 54)

    # Calculate best fit font size
    fontSize = calculateBestFitFontSize(context, width, height, texts, biggestFontSize)

    # Calculate positions
    currentX = hotasDetail.get('x')
    currentY = hotasDetail.get('y')
    maxX = hotasDetail.get('x') + hotasDetail.get('width')

    for text in texts:
        text['Size'] = fontSize
        context.font = text['Style']['Font']
        context.font_size = fontSize
        metrics = context.get_font_metrics(img, text['Text'], multiline=False)
        
        if currentX + int(metrics.text_width) > maxX:
            currentX = hotasDetail.get('x')
            currentY = currentY + fontSize
        
        text['X'] = currentX
        text['Y'] = currentY + int(metrics.ascender)
        currentX = currentX + int(metrics.text_width + metrics.character_width)

    # Center texts vertically
    textHeight = currentY + fontSize - hotasDetail.get('y')
    yOffset = int((height - textHeight) / 2) - int(fontSize / 6)
    for text in texts:
        text['Y'] = text['Y'] + yOffset

    return texts


def calculateBestFitFontSize(context, width, height, texts, biggestFontSize):
    """Calculate the best font size to fit texts in a box.
    
    Args:
        context: Drawing context
        width: Box width
        height: Box height
        texts: List of text dictionaries
        biggestFontSize: Starting font size
    
    Returns:
        Best fit font size
    """
    fontSize = biggestFontSize
    context.push()
    
    with Image(width=width, height=height) as img:
        fits = False
        while not fits:
            currentX = 0
            currentY = 0
            tooLong = False
            
            for text in texts:
                context.font = text['Style']['Font']
                context.font_size = fontSize
                metrics = context.get_font_metrics(img, text['Text'], multiline=False)
                
                if currentX + int(metrics.text_width) > width:
                    if currentX == 0:
                        tooLong = True
                        break
                    else:
                        currentX = 0
                        currentY = currentY + fontSize
                
                text['X'] = currentX
                text['Y'] = currentY + int(metrics.ascender)
                currentX = currentX + int(metrics.text_width + metrics.character_width)
            
            if not tooLong and currentY + metrics.text_height < height:
                fits = True
            else:
                fontSize = fontSize - 1
    
    context.pop()
    return fontSize


def calculateBestFontSize(context, text, hotasDetail, biggestFontSize):
    """Calculate the best font size for a single text in a box.
    
    Args:
        context: Drawing context
        text: Text string
        hotasDetail: Bounding box info
        biggestFontSize: Starting font size
    
    Returns:
        Tuple of (formatted_text, font_size, metrics)
    """
    width = hotasDetail.get('width')
    height = hotasDetail.get('height', 54)
    
    with Image(width=width, height=height) as img:
        fontSize = biggestFontSize
        fits = False
        
        while not fits:
            fitText = text
            context.font_size = fontSize
            metrics = context.get_font_metrics(img, fitText, multiline=False)
            
            if metrics.text_width <= hotasDetail.get('width'):
                fits = True
            else:
                lines = max(int(height / metrics.text_height), 1)
                if lines == 1:
                    fontSize = fontSize - 1
                else:
                    fitText = ''
                    minLineLength = int(len(text) / lines)
                    regex = r'.{%s}[^,]*, |.+' % minLineLength
                    matches = re.findall(regex, text)
                    for match in matches:
                        if fitText == '':
                            fitText = match
                        else:
                            fitText = '%s\n%s' % (fitText, match)

                    metrics = context.get_font_metrics(img, fitText, multiline=True)
                    if metrics.text_width <= hotasDetail.get('width'):
                        fits = True
                    else:
                        fontSize = fontSize - 1

    return (fitText, fontSize, metrics)
