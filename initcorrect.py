# ============================================================================
# VARKEN.PY - CORRECT INITIALIZATION (Line ~100-120)
# Replace your current DBManager initialization with this
# ============================================================================

# After you have: CONFIG = INIParser('/opt/Varken/data/varken.ini')

# Initialize database manager with proper error handling
#logger.info("Initializing database manager...")

try:
    # Use the enhanced parser if available
    if hasattr(CONFIG, 'get_enabled_databases'):
        enabled_dbs = CONFIG.get_enabled_databases()
        
        if not enabled_dbs:
            logger.critical("No enabled databases found in config!")
            logger.critical("Please set 'enabled = true' for at least one database section in varken.ini")
            sys.exit(1)
        
        logger.info(f"Found {len(enabled_dbs)} enabled database(s):")
        for db in enabled_dbs:
            logger.info(f"  - {db.db_type} at {db.url}:{db.port}")
        
        # Initialize with enabled databases only
        DBMANAGER = DBManager(enabled_dbs)
        logger.info(f"✓ Database manager initialized with {len(enabled_dbs)} backend(s)")
        
    elif hasattr(CONFIG, 'database_configs'):
        # Fallback: filter enabled databases manually
        enabled_dbs = [db for db in CONFIG.database_configs if db.enabled]
        
        if not enabled_dbs:
            logger.critical("No enabled databases found in config!")
            sys.exit(1)
        
        logger.info(f"Found {len(enabled_dbs)} enabled database(s)")
        DBMANAGER = DBManager(enabled_dbs)
        
    elif hasattr(CONFIG, 'influx_server'):
        # Legacy single InfluxDB configuration
        logger.info("Using legacy InfluxDB v1 configuration")
        DBMANAGER = DBManager(CONFIG.influx_server)
        logger.info("✓ Connected to InfluxDB v1")
        
    else:
        logger.critical("No database configuration found!")
        logger.critical("Please configure at least one database in varken.ini")
        sys.exit(1)
        
except Exception as e:
    logger.critical(f"Failed to initialize database manager: {e}")
    logger.critical("Check your database configuration and credentials")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Continue with rest of Varken.py...
