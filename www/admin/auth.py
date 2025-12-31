#!/usr/bin/env python3
"""
EDRefCard Admin Authentication

HTTP Basic Authentication for the admin panel.
Credentials are read from environment variables.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import request, Response


# Default credentials (override with environment variables)
ADMIN_USERNAME = os.environ.get('EDREFCARD_ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('EDREFCARD_ADMIN_PASS', 'changeme')

# Configure admin access logging
log_dir = Path(__file__).parent.parent / 'data'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'admin_access.log'

admin_logger = logging.getLogger('admin_access')
admin_logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_file)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
admin_logger.addHandler(handler)


def check_auth(username, password):
    """Check if username/password combination is valid.
    
    Args:
        username: Provided username
        password: Provided password
    
    Returns:
        True if valid, False otherwise
    """
    is_valid = username == ADMIN_USERNAME and password == ADMIN_PASSWORD
    
    # Log authentication attempts
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    if is_valid:
        admin_logger.info(
            f"SUCCESS - User: {username} | IP: {ip_address} | UA: {user_agent}"
        )
    else:
        admin_logger.warning(
            f"FAILED - User: {username} | IP: {ip_address} | UA: {user_agent}"
        )
    
    return is_valid


def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Authentication required.\n'
        'Please provide valid admin credentials.',
        401,
        {'WWW-Authenticate': 'Basic realm="EDRefCard Admin"'}
    )


def require_admin(f):
    """Decorator to require admin authentication for a route.
    
    Usage:
        @app.route('/admin/')
        @require_admin
        def admin_dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
