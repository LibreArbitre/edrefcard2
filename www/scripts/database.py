#!/usr/bin/env python3
"""
EDRefCard Database Module

SQLite database for storing configurations and device information.
"""

import sqlite3
import datetime
import pickle
from pathlib import Path
from contextlib import contextmanager

# Database file location
DB_PATH = None  # Set by init_db()


def init_db(db_path):
    """Initialize the database connection and create tables if needed.
    
    Args:
        db_path: Path to the SQLite database file
    """
    global DB_PATH
    DB_PATH = Path(db_path)
    
    # Create parent directory if needed
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Create tables
    with get_db() as conn:
        conn.executescript("""
            -- Configurations (reference cards)
            CREATE TABLE IF NOT EXISTS configurations (
                id TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                styling TEXT DEFAULT 'None',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_public INTEGER DEFAULT 1,
                is_featured INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                unhandled_devices_warnings TEXT DEFAULT '',
                device_warnings TEXT DEFAULT '',
                misconfiguration_warnings TEXT DEFAULT ''
            );
            
            -- Devices associated with a configuration
            CREATE TABLE IF NOT EXISTS config_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id TEXT NOT NULL,
                device_key TEXT NOT NULL,
                device_display_name TEXT,
                FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE CASCADE,
                UNIQUE(config_id, device_key)
            );
            
            -- Display groups selected for a configuration
            CREATE TABLE IF NOT EXISTS config_display_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                FOREIGN KEY (config_id) REFERENCES configurations(id) ON DELETE CASCADE,
                UNIQUE(config_id, group_name)
            );
            
            -- Create indexes
            CREATE INDEX IF NOT EXISTS idx_config_created ON configurations(created_at);
            CREATE INDEX IF NOT EXISTS idx_config_public ON configurations(is_public);
            CREATE INDEX IF NOT EXISTS idx_config_devices_config ON config_devices(config_id);
        """)


@contextmanager
def get_db():
    """Get a database connection context manager."""
    # DIAGNOSTIC
    if not DB_PATH.parent.exists():
        print(f"DB_CRIT: Parent dir {DB_PATH.parent} DOES NOT EXIST!")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ============== Configuration CRUD ==============

def create_configuration(config_id, description='', styling='None', display_groups=None,
                         devices=None, unhandled_warnings='', device_warnings='', 
                         misc_warnings='', created_at=None):
    """Create a new configuration in the database.
    
    Args:
        config_id: Unique 6-character identifier
        description: User description
        styling: Styling mode ('None', 'Group', 'Category', 'Modifier')
        display_groups: List of group names
        devices: Dictionary of device_key -> device_info
        unhandled_warnings: Warning about unsupported devices
        device_warnings: Device-specific warnings
        misc_warnings: Misconfiguration warnings
        created_at: Timestamp (defaults to now)
    """
    if created_at is None:
        created_at = datetime.datetime.now(datetime.timezone.utc)
    
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO configurations 
            (id, description, styling, created_at, unhandled_devices_warnings,
             device_warnings, misconfiguration_warnings)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (config_id, description, styling, created_at, 
              unhandled_warnings, device_warnings, misc_warnings))
        
        # Insert display groups
        if display_groups:
            conn.executemany("""
                INSERT OR IGNORE INTO config_display_groups (config_id, group_name)
                VALUES (?, ?)
            """, [(config_id, group) for group in display_groups])
        
        # Insert devices
        if devices:
            for device_key, device_info in devices.items():
                display_name = None
                if device_info and isinstance(device_info, dict):
                    display_name = device_info.get('Template', device_key)
                conn.execute("""
                    INSERT OR REPLACE INTO config_devices 
                    (config_id, device_key, device_display_name)
                    VALUES (?, ?, ?)
                """, (config_id, device_key, display_name))


def get_configuration(config_id):
    """Get a configuration by ID.
    
    Returns:
        Dictionary with config data or None
    """
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM configurations WHERE id = ?", (config_id,)
        ).fetchone()
        
        if row is None:
            return None
        
        config = dict(row)
        
        # Get display groups
        groups = conn.execute(
            "SELECT group_name FROM config_display_groups WHERE config_id = ?",
            (config_id,)
        ).fetchall()
        config['display_groups'] = [g['group_name'] for g in groups]
        
        # Get devices
        devices = conn.execute(
            "SELECT device_key, device_display_name FROM config_devices WHERE config_id = ?",
            (config_id,)
        ).fetchall()
        config['devices'] = {d['device_key']: d['device_display_name'] for d in devices}
        
        return config


def list_configurations(page=1, per_page=50, public_only=True, search=None, device_filter=None):
    """List configurations with pagination.
    
    Args:
        page: Page number (1-indexed)
        per_page: Items per page
        public_only: Only show public configurations
        search: Search term for description
        device_filter: Filter by device name
    
    Returns:
        Tuple of (list of configs, total count)
    """
    offset = (page - 1) * per_page
    params = []
    where_clauses = []
    
    if public_only:
        where_clauses.append("c.is_public = 1")
    
    if search:
        where_clauses.append("c.description LIKE ?")
        params.append(f"%{search}%")
    
    if device_filter:
        where_clauses.append("""
            c.id IN (SELECT config_id FROM config_devices WHERE device_display_name LIKE ?)
        """)
        params.append(f"%{device_filter}%")
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    with get_db() as conn:
        # Get total count
        count = conn.execute(
            f"SELECT COUNT(*) FROM configurations c WHERE {where_sql}",
            params
        ).fetchone()[0]
        
        # Get page of results
        rows = conn.execute(f"""
            SELECT c.*, GROUP_CONCAT(DISTINCT cd.device_display_name) as device_names
            FROM configurations c
            LEFT JOIN config_devices cd ON c.id = cd.config_id
            WHERE {where_sql}
            GROUP BY c.id
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()
        
        configs = [dict(row) for row in rows]
        
    return configs, count


def update_configuration(config_id, **kwargs):
    """Update a configuration.
    
    Args:
        config_id: Configuration ID
        **kwargs: Fields to update (description, is_public, is_featured)
    """
    allowed_fields = {'description', 'is_public', 'is_featured', 'styling'}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return
    
    set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [config_id]
    
    with get_db() as conn:
        conn.execute(
            f"UPDATE configurations SET {set_clause} WHERE id = ?",
            values
        )


def delete_configuration(config_id):
    """Delete a configuration and its associated files.
    
    Args:
        config_id: Configuration ID
    """
    with get_db() as conn:
        conn.execute("DELETE FROM configurations WHERE id = ?", (config_id,))


def get_configuration_stats():
    """Get statistics about configurations.
    
    Returns:
        Dictionary with stats
    """
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM configurations").fetchone()[0]
        public = conn.execute(
            "SELECT COUNT(*) FROM configurations WHERE is_public = 1"
        ).fetchone()[0]
        
        # Configs per day (last 30 days)
        daily = conn.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM configurations
            WHERE created_at >= DATE('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """).fetchall()
        
        # Most popular devices
        popular_devices = conn.execute("""
            SELECT device_display_name, COUNT(*) as count
            FROM config_devices
            WHERE device_display_name IS NOT NULL
            GROUP BY device_display_name
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()
        
        return {
            'total_configurations': total,
            'public_configurations': public,
            'daily_stats': [dict(d) for d in daily],
            'popular_devices': [dict(d) for d in popular_devices]
        }


# ============== Migration from Pickle ==============

def migrate_from_pickle(configs_path):
    """Migrate existing pickle files to SQLite.
    
    Args:
        configs_path: Path to the configs directory
        
    Returns:
        Tuple of (migrated_count, error_count)
    """
    configs_path = Path(configs_path)
    migrated = 0
    errors = 0
    
    for replay_path in configs_path.glob('**/*.replay'):
        try:
            with replay_path.open('rb') as f:
                data = pickle.load(f)
            
            config_id = replay_path.stem
            
            create_configuration(
                config_id=config_id,
                description=data.get('description', ''),
                styling=data.get('styling', 'None'),
                display_groups=data.get('displayGroups', []),
                devices=data.get('devices', {}),
                unhandled_warnings=data.get('unhandledDevicesWarnings', ''),
                device_warnings=data.get('deviceWarnings', ''),
                misc_warnings=data.get('misconfigurationWarnings', ''),
                created_at=data.get('timestamp')
            )
            migrated += 1
            
        except Exception as e:
            print(f"Error migrating {replay_path}: {e}")
            errors += 1
    
    return migrated, errors


def get_all_device_names():
    """Get all unique device names from configurations.
    
    Returns:
        List of device names
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT device_display_name 
            FROM config_devices 
            WHERE device_display_name IS NOT NULL
            ORDER BY device_display_name
        """).fetchall()
        
    return [r['device_display_name'] for r in rows]
