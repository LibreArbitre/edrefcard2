#!/usr/bin/env python3
"""
EDRefCard Utils Module

This module contains utility functions used across the application.
"""

import sys

# Key translation map for displaying keyboard keys
keymap = {
    'Key_LeftShift': '⇧',
    'Key_RightShift': '⇧',
    'Key_LeftAlt': 'Alt',
    'Key_RightAlt': 'Alt',
    'Key_LeftControl': 'Ctrl',
    'Key_RightControl': 'Ctrl',
    'Key_LeftBracket': '[',
    'Key_RightBracket': ']',
    'Key_SemiColon': ';',
    'Key_Apostrophe': "'",
    'Key_BackSlash': '\\',
    'Key_Comma': ',',
    'Key_Period': '.',
    'Key_Slash': '/',
    'Key_Equals': '=',
    'Key_Minus': '-',
    'Key_Grave': '`',
    'Key_Tab': '⇥',
    'Key_CapsLock': '⇪',
    'Key_Return': '↵',
    'Key_Backspace': '⌫',
    'Key_Space': '␣',
    'Key_Escape': 'Esc',
    'Key_Delete': 'Del',
    'Key_Insert': 'Ins',
    'Key_Home': 'Home',
    'Key_End': 'End',
    'Key_PageUp': 'PgUp',
    'Key_PageDown': 'PgDn',
    'Key_UpArrow': '↑',
    'Key_DownArrow': '↓',
    'Key_LeftArrow': '←',
    'Key_RightArrow': '→',
    'Key_Numpad_0': 'Num0',
    'Key_Numpad_1': 'Num1',
    'Key_Numpad_2': 'Num2',
    'Key_Numpad_3': 'Num3',
    'Key_Numpad_4': 'Num4',
    'Key_Numpad_5': 'Num5',
    'Key_Numpad_6': 'Num6',
    'Key_Numpad_7': 'Num7',
    'Key_Numpad_8': 'Num8',
    'Key_Numpad_9': 'Num9',
    'Key_Numpad_Divide': 'Num/',
    'Key_Numpad_Multiply': 'Num*',
    'Key_Numpad_Subtract': 'Num-',
    'Key_Numpad_Add': 'Num+',
    'Key_Numpad_Enter': 'Num↵',
    'Key_Numpad_Decimal': 'Num.',
    'Key_NumLock': 'NumLk',
    'Key_ScrollLock': 'ScrLk',
    'Key_Pause': 'Pause',
    'Key_PrintScreen': 'PrtSc',
}


def getFontPath(weight, style):
    """Get the path to a font file.
    
    Args:
        weight: Font weight ('Regular', 'Bold', 'SemiBold', etc.)
        style: Font style ('Normal', 'Italic')
        
    Returns:
        Relative path to the font file
    """
    if style == 'Normal':
        style = ''
    if weight == 'Regular' and style != '':
        weight = ''
    return '../fonts/Exo2.0-%s%s.otf' % (weight, style)


def transKey(key):
    """Translate a key code to a displayable string.
    
    Args:
        key: Key code string (e.g., 'Key_A', 'Key_Comma')
        
    Returns:
        Human-readable key name or symbol
    """
    if key is None:
        return None
    trans = keymap.get(key)
    if trans is None:
        trans = key.replace('Key_', '')
    return trans


RECENT_ERRORS = []

def logError(message):
    """Log an error message to stderr and a persistent file.
    
    Args:
        message: The error message to log
    """
    sys.stderr.write("EDRefCard: " + message)
    
    # Keep last 20 errors in memory
    global RECENT_ERRORS
    import datetime
    from pathlib import Path
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}\n"
    
    RECENT_ERRORS.append(f"[{timestamp}] {message}")
    if len(RECENT_ERRORS) > 50:
        RECENT_ERRORS.pop(0)

    # Persist to file in configs (which is a volume)
    try:
        # Assuming we are in www/scripts, go up to www/configs
        log_path = Path(__file__).parent.parent / 'configs' / 'error.log'
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(formatted_msg)
    except Exception as e:
        # DIAGNOSTIC: Check why log failed
        try:
            parent = Path(__file__).parent.parent / 'configs'
            sys.stderr.write(f"LOG_FAIL: Path '{log_path}' - Parent '{parent}' Exists? {parent.exists()} IsDir? {parent.is_dir()}\n")
            if parent.exists():
                 import os
                 sys.stderr.write(f"LOG_FAIL_LS: {os.listdir(str(parent))[:5]}\n")
        except:
            pass
        sys.stderr.write(f"Failed to log to file: {e}\n")
