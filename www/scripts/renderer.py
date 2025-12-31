#!/usr/bin/env python3
"""
EDRefCard Renderer Module

This module contains functions for generating reference card images
using the Wand/ImageMagick library.
"""

import re
from collections import OrderedDict

try:
    from wand.drawing import Drawing
    from wand.image import Image
    from wand.font import Font
    from wand.color import Color
except ImportError:
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
            for physicalKeySpec, physicalKey in physicalKeys.items():
                itemDevice = physicalKey.get('Device')
                itemKey = physicalKey.get('Key')

                if itemDevice not in imageDevices:
                    continue

                for modifier, bind in physicalKey.get('Binds').items():
                    for controlKey, control in bind.get('Controls').items():
                        bindInfo = {
                            'Control': control,
                            'Key': itemKey,
                            'Modifiers': []
                        }

                        if modifier != 'Unmodified':
                            for modifierKey, modifierControls in modifiers.items():
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
                for bindKey, bind in orderedOutputs.items():
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
        misconfigurationWarnings: Current misconfiguration warnings string
    
    Returns:
        True if image was created successfully
    """
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
    
    with Image(filename='../res/' + source + '.jpg') as sourceImg:
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
                        for controlKey, control in bind.get('Controls').items():
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
                            
                            for controlKey, control in bind.get('Controls').items():
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
