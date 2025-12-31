#!/usr/bin/env python3
"""
EDRefCard Models Module

This module contains the core data models and configuration classes.
"""

import os
import string
import random
import pickle
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin


class Config:
    """Configuration manager for EDRefCard.
    
    Handles paths for storing and retrieving binding configurations,
    including file paths and URLs for generated reference cards.
    """
    
    # Class-level configuration - can be overridden by Flask app
    _dir_root = None
    _web_root = None
    
    @classmethod
    def setDirRoot(cls, path):
        """Set the root directory for configs (for Flask integration)."""
        cls._dir_root = Path(path).resolve()
    
    @classmethod
    def setWebRoot(cls, url):
        """Set the web root URL (for Flask integration)."""
        cls._web_root = url
    
    @staticmethod
    def dirRoot():
        """Get the root directory for the application."""
        if Config._dir_root is not None:
            return Config._dir_root
        return Path(os.environ.get('CONTEXT_DOCUMENT_ROOT', '..')).resolve()
    
    @staticmethod    
    def webRoot():
        """Get the web root URL for generating links."""
        # Try to use Flask request context if available
        try:
            from flask import has_request_context, request
            if has_request_context():
                return request.url_root
        except ImportError:
            pass
            
        if Config._web_root is not None:
            return Config._web_root
        return urljoin(os.environ.get('SCRIPT_URI', 'https://edrefcard.info/'), '/')
    
    @staticmethod
    def newRandom():
        """Create a new Config with a random unique name."""
        config = Config(Config.randomName())
        while config.exists():
            config = Config(Config.randomName())
        return config
    
    def __init__(self, name):
        """Initialize a Config with the given name.
        
        Args:
            name: The configuration identifier (6 lowercase letters)
            
        Raises:
            ValueError: If name is empty
        """
        if not name:
            raise ValueError('Config must have a name')
        self.name = name
    
    def __repr__(self):
        return "Config('%s')" % self.name
    
    @staticmethod
    def randomName():
        """Generate a random 6-character lowercase name."""
        name = ''.join(random.choice(string.ascii_lowercase) for x in range(6))
        return name
    
    @staticmethod
    def configsPath():
        """Get the path to the configs directory."""
        return Config.dirRoot() / 'configs'
        
    def path(self):
        """Get the base path for this config's files."""
        path = Config.configsPath() / self.name[:2] / self.name
        return path
    
    def pathWithNameAndSuffix(self, name, suffix):
        """Get a path with an additional name component and suffix.
        
        Args:
            name: Additional name component (e.g., device template name)
            suffix: File suffix (must start with '.')
            
        Returns:
            Path object for the file
        """
        newName = '-'.join([self.name, name])
        p = self.path().with_name(newName)
        return p.with_suffix(suffix)
    
    def pathWithSuffix(self, suffix):
        """Get the path with the given file suffix.
        
        Args:
            suffix: File suffix (must start with '.')
            
        Returns:
            Path object for the file
        """
        return self.path().with_suffix(suffix)
        
    def exists(self):
        """Check if this config already exists on disk."""
        return self.path().exists()
        
    def makeDir(self):
        """Create the directory structure for this config."""
        fullPath = self.path()
        dirPath = fullPath.parent
        dirPath.mkdir(parents=True, exist_ok=True)
        
    def refcardURL(self):
        """Get the URL to view this reference card."""
        url = urljoin(Config.webRoot(), "binds/%s" % self.name)
        return url
        
    def bindsURL(self):
        """Get the URL to download the binds file."""
        url = urljoin(Config.webRoot(), "configs/%s.binds" % self.name)
        return url

    @staticmethod
    def unpickle(path):
        """Load a pickled config object from a file.
        
        Args:
            path: Path to the .replay file
            
        Returns:
            Dictionary with config data including runID
        """
        with path.open('rb') as file:
            obj = pickle.load(file)
            obj['runID'] = path.stem
        return obj
            
    @staticmethod
    def allConfigs(sortKey=None):
        """Get all saved configurations.
        
        Args:
            sortKey: Optional function to sort the configs
            
        Returns:
            List of config dictionaries
        """
        configsPath = Config.configsPath()
        if not configsPath.exists():
            return []
        picklePaths = list(configsPath.glob('**/*.replay'))
        objs = [Config.unpickle(path) for path in picklePaths]
        if sortKey is not None:
            objs.sort(key=sortKey)
        return objs


class Mode(Enum):
    """Operating modes for the application."""
    invalid = 0
    blocks = 1
    list = 2
    replay = 3
    generate = 4
    listDevices = 5


class Errors:
    """Container for error and warning messages during processing."""
    
    def __init__(
            self,
            unhandledDevicesWarnings='',
            deviceWarnings='',
            misconfigurationWarnings='',
            errors=''
        ):
        """Initialize error container.
        
        Args:
            unhandledDevicesWarnings: Warning about unsupported devices
            deviceWarnings: Warnings about specific device issues
            misconfigurationWarnings: Warnings about misconfigured controls
            errors: Critical errors that prevent processing
        """
        self.unhandledDevicesWarnings = unhandledDevicesWarnings
        self.deviceWarnings = deviceWarnings
        self.misconfigurationWarnings = misconfigurationWarnings
        self.errors = errors
    
    def __repr__(self):
        return ("Errors(unhandledDevicesWarnings='%s', deviceWarnings='%s', "
                "misconfigurationWarnings='%s', errors='%s')" 
                % (self.unhandledDevicesWarnings, self.deviceWarnings, 
                   self.misconfigurationWarnings, self.errors))
    
    def hasErrors(self):
        """Check if there are any critical errors."""
        return bool(self.errors)
    
    def hasWarnings(self):
        """Check if there are any warnings."""
        return bool(self.unhandledDevicesWarnings or 
                    self.deviceWarnings or 
                    self.misconfigurationWarnings)
