#!/usr/bin/env python3
"""
EDRefCard Styles Module

This module contains styling constants for rendering reference cards,
including colors and fonts for different control groups and categories.
"""

from wand.color import Color

from .utils import getFontPath


# Command group styling - used when styling by group type
groupStyles = {
    'General': {'Color': Color('Black'), 'Font': getFontPath('Regular', 'Normal')},
    'Misc': {'Color': Color('Black'), 'Font': getFontPath('Regular', 'Normal')},
    'Modifier': {'Color': Color('Black'), 'Font': getFontPath('Bold', 'Normal')},
    'Galaxy map': {'Color': Color('ForestGreen'), 'Font': getFontPath('Regular', 'Normal')},
    'Holo-Me': {'Color': Color('Sienna'), 'Font': getFontPath('Regular', 'Normal')},
    'Multicrew': {'Color': Color('SteelBlue'), 'Font': getFontPath('Bold', 'Normal')},
    'Fighter': {'Color': Color('DarkSlateBlue'), 'Font': getFontPath('Regular', 'Normal')},
    'Camera': {'Color': Color('OliveDrab'), 'Font': getFontPath('Regular', 'Normal')},
    'Head look': {'Color': Color('IndianRed'), 'Font': getFontPath('Regular', 'Normal')},
    'Ship': {'Color': Color('Crimson'), 'Font': getFontPath('Regular', 'Normal')},
    'SRV': {'Color': Color('MediumPurple'), 'Font': getFontPath('Regular', 'Normal')},
    'Scanners': {'Color': Color('DarkOrchid'), 'Font': getFontPath('Regular', 'Normal')},
    'UI': {'Color': Color('DarkOrange'), 'Font': getFontPath('Regular', 'Normal')},
    'OnFoot': {'Color': Color('CornflowerBlue'), 'Font': getFontPath('Regular', 'Normal')},
}

# Command category styling - used when styling by category
categoryStyles = {
    'General': {'Color': Color('DarkSlateBlue'), 'Font': getFontPath('Regular', 'Normal')},
    'Combat': {'Color': Color('Crimson'), 'Font': getFontPath('Regular', 'Normal')},
    'Social': {'Color': Color('ForestGreen'), 'Font': getFontPath('Regular', 'Normal')},
    'Navigation': {'Color': Color('Black'), 'Font': getFontPath('Regular', 'Normal')},
    'UI': {'Color': Color('DarkOrange'), 'Font': getFontPath('Regular', 'Normal')},
}


class ModifierStyles:
    """Styling for modifier keys.
    
    Modifiers are numbered and each gets a distinct color to help
    users quickly identify which modifier is needed for each binding.
    """
    
    styles = [
        {'Color': Color('Black'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('Crimson'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('ForestGreen'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('DarkSlateBlue'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('DarkOrange'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('DarkOrchid'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('SteelBlue'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('Sienna'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('IndianRed'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('CornflowerBlue'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('OliveDrab'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('MediumPurple'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('DarkSalmon'), 'Font': getFontPath('Regular', 'Normal')},
        {'Color': Color('LightSlateGray'), 'Font': getFontPath('Regular', 'Normal')},
    ]

    @staticmethod
    def index(num):
        """Get the style for a modifier number.
        
        Args:
            num: The modifier number (wraps around if > len(styles))
            
        Returns:
            Style dictionary with 'Color' and 'Font' keys
        """
        i = num % len(ModifierStyles.styles)
        return ModifierStyles.styles[i]
