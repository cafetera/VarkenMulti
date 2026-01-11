#!/usr/bin/env python3
"""
Debug script to check Varken database configuration
Run this to see what's wrong with your config
"""

import sys
sys.path.insert(0, '/opt/Varken')

from configparser import ConfigParser

print("=" * 60)
print("Varken Database Configuration Debug")
print("=" * 60)
print()

# Read the config file
config_path = '/opt/Varken/data/varken.ini'
config = ConfigParser()

try:
    config.read(config_path)
    print(f"✓ Successfully read config file: {config_path}")
    print()
except Exception as e:
    print(f"✗ Error reading config file: {e}")
    sys.exit(1)

# Check all sections
print("Available sections in config:")
for section in config.sections():
    print(f"  - [{section}]")
print()

# Check for database sections
db_sections = ['INFLUXDB', 'INFLUXDB2', 'INFLUXDB3', 'TIMESCALEDB', 'QUESTDB']
print("Database sections found:")
for section in db_sections:
    if config.has_section(section):
        enabled = config.getboolean(section, 'enabled', fallback=False)
        hostname = config.get(section, 'hostname', fallback='NOT SET')
        print(f"  ✓ [{section}]")
        print(f"    - enabled: {enabled}")
        print(f"    - hostname: {hostname}")
        
        # Show all options in this section
        print(f"    - All settings:")
        for key, value in config.items(section):
            # Hide passwords
            if 'password' in key.lower() or 'token' in key.lower():
                value = '***HIDDEN***'
            print(f"      {key} = {value}")
        print()
    else:
        print(f"  ✗ [{section}] - NOT FOUND")

print()
print("=" * 60)
print("Testing configuration parsing...")
print("=" * 60)
print()

try:
    from varken.iniparser_v2 import EnhancedINIParser
    
    parser = EnhancedINIParser(config_path)
    
    print(f"✓ Configuration parsed successfully")
    print(f"  Database configs found: {len(parser.database_configs)}")
    print(f"  Enabled databases: {len(parser.get_enabled_databases())}")
    print()
    
    for i, db_config in enumerate(parser.database_configs, 1):
        print(f"{i}. {db_config.db_type}")
        print(f"   - URL: {db_config.url}:{db_config.port}")
        print(f"   - Database: {db_config.database}")
        print(f"   - Enabled: {db_config.enabled}")
        print()
    
    if len(parser.get_enabled_databases()) == 0:
        print("⚠ WARNING: No databases are enabled!")
        print("  Make sure at least one database section has 'enabled = true'")
        
except ImportError as e:
    print(f"✗ Error importing iniparser_v2: {e}")
    print("  Make sure iniparser_v2.py is in /opt/Varken/varken/")
except Exception as e:
    print(f"✗ Error parsing config: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Testing database connections...")
print("=" * 60)
print()

try:
    from varken.dbmanager_v2 import MultiDBManager
    from varken.iniparser_v2 import EnhancedINIParser
    
    parser = EnhancedINIParser(config_path)
    enabled_dbs = parser.get_enabled_databases()
    
    if not enabled_dbs:
        print("✗ No enabled databases found - cannot test connections")
    else:
        print(f"Attempting to connect to {len(enabled_dbs)} database(s)...")
        print()
        
        for db_config in enabled_dbs:
            print(f"Testing {db_config.db_type} at {db_config.url}:{db_config.port}...")
            try:
                # Try to initialize just this one backend
                from varken.dbmanager_v2 import (
                    InfluxDBv1Backend, InfluxDBv2Backend, InfluxDBv3Backend,
                    TimescaleDBBackend, QuestDBBackend
                )
                
                backend_map = {
                    'influxdb1': InfluxDBv1Backend,
                    'influxdb2': InfluxDBv2Backend,
                    'influxdb3': InfluxDBv3Backend,
                    'timescale': TimescaleDBBackend,
                    'questdb': QuestDBBackend
                }
                
                backend_class = backend_map.get(db_config.db_type.lower())
                if backend_class:
                    backend = backend_class(db_config)
                    if backend.connect():
                        print(f"  ✓ Successfully connected!")
                    else:
                        print(f"  ✗ Connection failed (check logs above)")
                else:
                    print(f"  ✗ Unknown database type: {db_config.db_type}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
            print()
        
except ImportError as e:
    print(f"✗ Error importing dbmanager_v2: {e}")
    print("  Make sure dbmanager_v2.py is in /opt/Varken/varken/")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Recommendations:")
print("=" * 60)
print()
print("1. Make sure at least one database section has 'enabled = true'")
print("2. Verify database credentials are correct")
print("3. Ensure databases are running and accessible")
print("4. Check firewall/network connectivity")
print()
