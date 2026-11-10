#!/usr/bin/env python3
"""
EDRefCard Models Module

This module contains the core data models and configuration classes.
"""

import os
import re
import secrets
import string
import random
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
    _configs_path = None
    
    @classmethod
    def setDirRoot(cls, path):
        """Set the root directory for configs (for Flask integration)."""
        cls._dir_root = Path(path).resolve()
        
    @classmethod
    def setConfigsPath(cls, path):
        """Set the explicit path to the configs directory."""
        cls._configs_path = Path(path).resolve()
    
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
    def configsPath():
        """Get the path to the configs directory."""
        if Config._configs_path is not None:
            return Config._configs_path
        return Config.dirRoot() / 'configs'
    
    @staticmethod
    def webRoot():
        """Get the web root URL for generating links."""
        # APP_URL is the configured external origin. A reverse proxy can leave
        # request.url_root on HTTP even when the visitor used HTTPS.
        if Config._web_root is not None:
            return Config._web_root
        # Try to use Flask request context if available
        try:
            from flask import has_request_context, request
            if has_request_context():
                return request.url_root
        except ImportError:
            pass
            
        return urljoin(os.environ.get('SCRIPT_URI', 'https://edrefcard.info/'), '/')
    
    @staticmethod
    def newRandom():
        """Create a new Config with a random unique name."""
        config = Config(Config.randomName())
        while config.exists():
            config = Config(Config.randomName())
        return config
    
    @staticmethod
    def claimUnique(base_id, is_taken=None):
        """Reserve a free config id derived from base_id and return its Config.

        The id is claimed by atomically creating its (empty) .binds file, so
        two simultaneous uploads of the same filename can never share an id,
        and an existing config is never overwritten. Nearly every upload is
        called Custom.4.2.binds: the old "append 3 random letters once,
        without re-checking" scheme was bound to overwrite a previous card.

        Args:
            base_id: slug to start from (used as is when free)
            is_taken: optional callable(id) -> bool for ids reserved
                elsewhere (database rows whose source file is gone)
        """
        base_id = (base_id or '')[:80].strip('-')
        alphabet = string.ascii_lowercase + string.digits
        attempt = 0
        while True:
            if attempt == 0 and base_id:
                name = base_id
            else:
                # 4 characters, growing if a prefix ever gets crowded
                suffix = ''.join(secrets.choice(alphabet) for _ in range(4 + attempt // 20))
                name = f'{base_id}-{suffix}' if base_id else Config.randomName() + suffix
            attempt += 1
            config = Config(name)
            if config.path().exists() or (is_taken is not None and is_taken(name)):
                continue
            config.makeDir()
            try:
                with open(config.pathWithSuffix('.binds'), 'x'):
                    pass
            except FileExistsError:
                continue
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
        """Check if this config already exists on disk.

        The bare base path is never created (only suffixed files like
        <id>.binds are), so probe the .binds file too: otherwise same-named
        uploads silently reuse the run id, overwrite the previous config and
        the browser serves stale cached card images.
        """
        return self.path().exists() or self.pathWithSuffix('.binds').exists()
        
    @staticmethod
    def isValidName(name):
        """True when name is a plausible config id (slug or legacy 6 letters).

        Ids are generated by slugify() or randomName(); anything else coming
        from a URL (dots, slashes, glob or HTML characters) is rejected before
        it reaches the filesystem or an error page.
        """
        return isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,200}', name) is not None

    def ownedFiles(self, other_ids=()):
        """Files on disk that belong to this config only.

        Every config sharing the first two characters of its id lives in the
        same directory, and ids can be prefixes of one another ('custom-4-2'
        vs 'custom-4-2-abc'), so neither the directory nor a '<id>-*' glob
        identifies one config. A file is owned when it is '<id>.binds' or
        starts with '<id>-', unless a longer sibling id also matches it.

        Args:
            other_ids: extra known config ids (e.g. from the database) for
                siblings whose .binds source is no longer on disk.
        """
        folder = self.path().parent
        if not folder.is_dir():
            return []
        prefix = self.name + '-'
        siblings = {p.stem for p in folder.iterdir()
                    if p.is_file() and p.suffix == '.binds'}
        siblings.update(other_ids)
        longer = [s + '-' for s in siblings if s.startswith(prefix)]
        longer_binds = {s + '.binds' for s in siblings if s.startswith(prefix)}
        owned = []
        for p in sorted(folder.iterdir()):
            if not p.is_file():
                continue
            if p.name == self.name + '.binds':
                owned.append(p)
            elif (p.name.startswith(prefix) and p.name not in longer_binds
                  and not any(p.name.startswith(other) for other in longer)):
                owned.append(p)
        return owned

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
