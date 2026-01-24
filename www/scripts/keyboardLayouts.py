# SIMPLIFIED: Minimal keyboard layouts for basic visualization
# For full implementation with ISO/Cyrillic, see migration_guide.md and PR #39
#
# This is a simplified version supporting ANSI 104-key layout only.
# Each entry maps Elite Dangerous key names to their visual representation
# on a standard ANSI keyboard.

keyboardLayouts = {
    # ANSI 104-key layout - Most common in North America
    'ANSI 104': {
        # Main alphanumeric keys
        'Key_Escape': 'Esc',
        'Key_1': '1',
        'Key_2': '2',
        'Key_3': '3',
        'Key_4': '4',
        'Key_5': '5',
        'Key_6': '6',
        'Key_7': '7',
        'Key_8': '8',
        'Key_9': '9',
        'Key_0': '0',
        'Key_Minus': '-',
        'Key_Equals': '=',
        'Key_Backspace': 'Backspace',
        
        # Tab row
        'Key_Tab': 'Tab',
       'Key_Q': 'Q',
        'Key_W': 'W',
        'Key_E': 'E',
        'Key_R': 'R',
        'Key_T': 'T',
        'Key_Y': 'Y',
        'Key_U': 'U',
        'Key_I': 'I',
        'Key_O': 'O',
        'Key_P': 'P',
        'Key_LeftBracket': '[',
        'Key_RightBracket': ']',
        'Key_BackSlash': '\\',
        
        # Caps Lock row
        'Key_CapsLock': 'Caps',
        'Key_A': 'A',
        'Key_S': 'S',
        'Key_D': 'D',
        'Key_F': 'F',
        'Key_G': 'G',
        'Key_H': 'H',
        'Key_J': 'J',
        'Key_K': 'K',
        'Key_L': 'L',
        'Key_SemiColon': ';',
        'Key_Apostrophe': "'",
        'Key_Enter': 'Enter',
        
        # Shift row
        'Key_LeftShift': 'L Shift',
        'Key_Z': 'Z',
        'Key_X': 'X',
        'Key_C': 'C',
        'Key_V': 'V',
        'Key_B': 'B',
        'Key_N': 'N',
        'Key_M': 'M',
        'Key_Comma': ',',
        'Key_Period': '.',
        'Key_Slash': '/',
        'Key_RightShift': 'R Shift',
        
        # Bottom row
        'Key_LeftControl': 'L Ctrl',
        'Key_LeftAlt': 'L Alt',
        'Key_Space': 'Space',
        'Key_RightAlt': 'R Alt',
        'Key_RightControl': 'R Ctrl',
        
        # Function keys
        'Key_F1': 'F1',
        'Key_F2': 'F2',
        'Key_F3': 'F3',
        'Key_F4': 'F4',
        'Key_F5': 'F5',
        'Key_F6': 'F6',
        'Key_F7': 'F7',
        'Key_F8': 'F8',
        'Key_F9': 'F9',
        'Key_F10': 'F10',
        'Key_F11': 'F11',
        'Key_F12': 'F12',
        
        # Navigation cluster
        'Key_PrintScreen': 'PrtSc',
        'Key_ScrollLock': 'ScrLk',
        'Key_Pause': 'Pause',
        'Key_Insert': 'Ins',
        'Key_Home': 'Home',
        'Key_PageUp': 'PgUp',
        'Key_Delete': 'Del',
        'Key_End': 'End',
        'Key_PageDown': 'PgDn',
        
        # Arrow keys
        'Key_UpArrow': '↑',
        'Key_LeftArrow': '←',
        'Key_DownArrow': '↓',
        'Key_RightArrow': '→',
        
        # Numpad
        'Key_NumLock': 'Num',
        'Key_Numpad_Divide': 'Num /',
        'Key_Numpad_Multiply': 'Num *',
        'Key_Numpad_Subtract': 'Num -',
        'Key_Numpad_7': 'Num 7',
        'Key_Numpad_8': 'Num 8',
        'Key_Numpad_9': 'Num 9',
        'Key_Numpad_Add': 'Num +',
        'Key_Numpad_4': 'Num 4',
        'Key_Numpad_5': 'Num 5',
        'Key_Numpad_6': 'Num 6',
        'Key_Numpad_1': 'Num 1',
        'Key_Numpad_2': 'Num 2',
        'Key_Numpad_3': 'Num 3',
        'Key_Numpad_Enter': 'Num Enter',
        'Key_Numpad_0': 'Num 0',
        'Key_Numpad_Decimal': 'Num .',
        
        # Additional keys
        'Key_Grave': '`',
        'Key_Application': 'Menu',
        'Key_LeftWindows': 'L Win',
        'Key_RightWindows': 'R Win',
    },
    
    # ISO 105 and Cyrillic layouts not implemented in simplified version
    # See migration_guide.md for full implementation
}

# Keyboard layout name mapping for UI
KEYBOARD_LAYOUT_NAMES = {
    'ansi': 'ANSI 104',
    'iso': 'ISO 105',  # Not implemented in simplified version
    'cyrillic': 'ЙЦУКЕН',  # Not implemented in simplified version
}
