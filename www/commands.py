import click
import shutil
import time
import re
from pathlib import Path
from flask.cli import with_appcontext
from scripts.utils import logError

@click.command('clean-cache')
@click.option('--days', default=1, help='Delete files older than X days')
@with_appcontext
def clean_cache_command(days):
    """Delete generated images older than the specified number of days."""
    from flask import current_app
    
    configs_dir = current_app.config['CONFIGS_FOLDER']
    if not configs_dir.exists():
        click.echo(f"Configs directory not found: {configs_dir}")
        return

    now = time.time()
    cutoff = now - (days * 86400)
    count = 0
    
    click.echo(f"Cleaning files older than {days} days in {configs_dir}...")
    
    for ext in ['*.jpg', '*.svg']:
        for file_path in configs_dir.glob(ext):
            if file_path.stat().st_ctime < cutoff:
                try:
                    file_path.unlink()
                    count += 1
                except OSError as e:
                    click.echo(f"Error deleting {file_path}: {e}")
    
    click.echo(f"Deleted {count} files.")


@click.command('find-unsupported')
@click.argument('logfile', type=click.Path(exists=True), required=False)
@with_appcontext
def find_unsupported_command(logfile):
    """Extract unsupported controls from logs.
    
    If no logfile is provided, it will check the standard error log location 
    if configured, or warn the user.
    """
    if not logfile:
        click.echo("Please provide a log file to analyze.")
        # In a real deployed env, we might default to /var/log/edrefcard.err
        return

    pattern = re.compile(r'.*No control for (.+)')
    unsupported = set()
    
    try:
        with open(logfile, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    unsupported.add(match.group(1))
        
        if unsupported:
            click.echo(f"Found {len(unsupported)} unsupported controls:")
            for control in sorted(unsupported):
                click.echo(control)
        else:
            click.echo("No unsupported controls found in the log.")
            
    except Exception as e:
        click.echo(f"Error reading log file: {e}")


@click.command('migrate-legacy')
@with_appcontext
def migrate_legacy_command():
    """Migrate legacy pickle configurations to SQLite."""
    from scripts import database
    from scripts.models import Config
    
    configs_path = Config.configsPath()
    if not configs_path.exists():
        click.echo(f"Configs directory not found: {configs_path}")
        return
        
    click.echo(f"Migrating from {configs_path}...")
    migrated, errors = database.migrate_from_pickle(configs_path)
    click.echo(f"Migration complete: {migrated} migrated, {errors} errors.")


@click.command('import-defaults')
@click.option('--limit', default=None, type=int, help='Limit number of files to import')
@with_appcontext
def import_defaults_command(limit):
    """Import default bindings from bindings/Defaults 3.3."""
    from flask import current_app
    from scripts import database, parser
    from scripts.models import Config, Errors
    
    # Path to Defaults 3.3 relative to www root (parent of www is project root)
    # www/../bindings/Defaults 3.3
    defaults_dir = current_app.config['WWW_DIR'].parent / 'bindings' / 'Defaults 3.3'
    
    if not defaults_dir.exists():
        click.echo(f"Defaults directory not found: {defaults_dir}")
        return

    click.echo(f"Importing defaults from {defaults_dir}...")
    
    count = 0
    errors_count = 0
    
    # Standard display groups for defaults
    display_groups = ['Ship', 'SRV', 'OnFoot', 'UI', 'Galaxy map', 'Head look', 'Scanners', 'Fighter', 'Multicrew', 'Camera', 'Holo-Me', 'Misc']
    
    bind_files = list(defaults_dir.glob('*.binds'))
    if limit:
        bind_files = bind_files[:limit]
        
    for bind_file in bind_files:
        try:
            # Create a new config with random ID
            config = Config.newRandom()
            config.makeDir()
            
            # Read and parse
            with bind_file.open('r', encoding='utf-8') as f:
                xml = f.read()
            
            # Save the .binds file (required for display)
            binds_path = config.pathWithSuffix('.binds')
            with open(str(binds_path), 'w', encoding='utf-8') as f:
                f.write(xml)
                
            parse_errors = Errors()
            (physicalKeys, modifiers, devices) = parser.parseBindings(
                config.name, xml, display_groups, parse_errors
            )
            
            if parse_errors.hasErrors():
                click.echo(f"Skipping {bind_file.name}: Parsing error")
                errors_count += 1
                continue
                
            # Create description from filename
            description = f"Default: {bind_file.stem}"
            
            # Save .replay file (crucial for rendering)
            parser.saveReplayInfo(
                config=config,
                description=description,
                styling='None',
                displayGroups=display_groups,
                devices=devices,
                errors=parse_errors
            )
            
            # Save to database
            # Extract warnings for DB
            database.create_configuration(
                config_id=config.name,
                description=description,
                styling='None',
                display_groups=display_groups,
                devices=devices,
                unhandled_warnings=parse_errors.unhandledDevicesWarnings,
                device_warnings=parse_errors.deviceWarnings,
                misc_warnings=parse_errors.misconfigurationWarnings
            )
            
            count += 1
            if count % 10 == 0:
                click.echo(f"Imported {count} configurations...")
                
        except Exception as e:
            click.echo(f"Error importing {bind_file.name}: {e}")
            errors_count += 1

    click.echo(f"Import complete: {count} imported, {errors_count} errors.")
