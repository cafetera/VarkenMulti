#!/usr/bin/env python3
"""
Test what CONFIG.database_configs actually contains
"""

import sys
sys.path.insert(0, '/opt/Varken')

from varken.iniparser_v2 import EnhancedINIParser

print("=" * 60)
print("Testing CONFIG object")
print("=" * 60)

CONFIG = EnhancedINIParser('/opt/Varken/data/varken.ini')

print(f"\nCONFIG object type: {type(CONFIG)}")
print(f"Has 'database_configs' attribute: {hasattr(CONFIG, 'database_configs')}")
print(f"Has 'get_enabled_databases' method: {hasattr(CONFIG, 'get_enabled_databases')}")

if hasattr(CONFIG, 'database_configs'):
    print(f"\nCONFIG.database_configs type: {type(CONFIG.database_configs)}")
    print(f"CONFIG.database_configs length: {len(CONFIG.database_configs)}")
    print(f"CONFIG.database_configs content:")
    for i, db in enumerate(CONFIG.database_configs):
        print(f"  {i}: {db}")
        print(f"      Type: {type(db)}")
        print(f"      db_type: {db.db_type}")
        print(f"      enabled: {db.enabled}")
        print(f"      url: {db.url}:{db.port}")

if hasattr(CONFIG, 'get_enabled_databases'):
    enabled = CONFIG.get_enabled_databases()
    print(f"\nCONFIG.get_enabled_databases() length: {len(enabled)}")
    for i, db in enumerate(enabled):
        print(f"  {i}: {db.db_type} at {db.url}:{db.port} (enabled={db.enabled})")

print("\n" + "=" * 60)
print("Testing DBManager initialization")
print("=" * 60)

try:
    from varken.dbmanager_v2 import DBManager
    
    # This is what Varken.py line 114 is doing
    print("\nAttempting: DBManager(CONFIG.database_configs)")
    print(f"Passing type: {type(CONFIG.database_configs)}")
    print(f"Passing value: {CONFIG.database_configs}")
    
    DBMANAGER = DBManager(CONFIG.database_configs)
    print("✓ SUCCESS!")
    
except Exception as e:
    print(f"✗ FAILED: {e}")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Trying alternative initialization")
    print("=" * 60)
    
    try:
        print("\nAttempting: DBManager(CONFIG.get_enabled_databases())")
        enabled_dbs = CONFIG.get_enabled_databases()
        print(f"Passing type: {type(enabled_dbs)}")
        print(f"Passing length: {len(enabled_dbs)}")
        print(f"Passing value: {enabled_dbs}")
        
        DBMANAGER = DBManager(enabled_dbs)
        print("✓ SUCCESS with get_enabled_databases()!")
        
    except Exception as e2:
        print(f"✗ ALSO FAILED: {e2}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Recommendation")
print("=" * 60)
print("\nIn Varken.py line 114, change from:")
print("  DBMANAGER = DBManager(CONFIG.database_configs)")
print("\nTo:")
print("  DBMANAGER = DBManager(CONFIG.get_enabled_databases())")
