#!/usr/bin/env python3
"""
EDRefCard Admin Authentication

HTTP Basic Authentication for the admin panel.
Credentials are read from environment variables.
"""

import os
from functools import wraps
from flask import request, Response


# Default credentials (override with environment variables)
ADMIN_USERNAME = os.environ.get('EDREFCARD_ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('EDREFCARD_ADMIN_PASS', 'changeme')


def check_auth(username, password):
    """Check if username/password combination is valid.
    
    Args:
        username: Provided username
        password: Provided password
    
    Returns:
        True if valid, False otherwise
    """
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


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
