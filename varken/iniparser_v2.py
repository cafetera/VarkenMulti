"""
Enhanced INI Parser for Varken with Multi-Database Support
Supports configuration for multiple database backends
"""

from configparser import ConfigParser
from typing import List, Optional
from dataclasses import dataclass
from varken.dbmanager_v2 import DatabaseConfig


@dataclass
class InfluxServer:
    """Legacy InfluxDB server configuration"""
    url: str
    port: int
    username: str
    password: str
    ssl: bool
    verify_ssl: bool


@dataclass
class TautulliServer:
    """Tautulli server configuration"""
    id: int
    url: str
    fallback_ip: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    get_activity: bool
    get_activity_run_seconds: int
    get_stats: bool
    get_stats_run_seconds: int
    maxmind_license_key: Optional[str] = None


@dataclass
class SonarrServer:
    """Sonarr server configuration"""
    id: int
    url: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    missing_days: int
    missing_days_run_seconds: int
    future_days: int
    future_days_run_seconds: int
    queue: bool
    queue_run_seconds: int


@dataclass
class RadarrServer:
    """Radarr server configuration"""
    id: int
    url: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    queue: bool
    queue_run_seconds: int
    get_missing: bool
    get_missing_run_seconds: int


@dataclass
class LidarrServer:
    """Lidarr server configuration"""
    id: int
    url: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    missing_days: int
    missing_days_run_seconds: int
    future_days: int
    future_days_run_seconds: int
    queue: bool
    queue_run_seconds: int


@dataclass
class OmbiServer:
    """Ombi server configuration"""
    id: int
    url: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    get_request_type_counts: bool
    request_type_run_seconds: int
    get_request_total_counts: bool
    request_total_run_seconds: int
    get_issue_status_counts: bool
    issue_status_run_seconds: int


@dataclass
class SickChillServer:
    """SickChill server configuration"""
    id: int
    url: str
    api_key: str  # Changed from apikey to api_key
    ssl: bool
    verify_ssl: bool
    get_missing: bool
    get_missing_run_seconds: int


@dataclass
class UniFiServer:
    """UniFi server configuration"""
    id: int
    url: str
    username: str
    password: str
    site: str
    usg_name: str
    ssl: bool
    verify_ssl: bool
    get_usg_stats_run_seconds: int


class EnhancedINIParser:
    """
    Enhanced configuration parser supporting multiple database backends
    """
    
    def __init__(self, config_path: str):
        self.config = ConfigParser()
        self.config.read(config_path)
        
        # Parse all database configurations
        self.database_configs: List[DatabaseConfig] = []
        self._parse_databases()
        
        # Legacy support - create influx_server if InfluxDB v1 is configured
        self.influx_server = self._create_legacy_influx_server()
        
        # Parse other sections (sonarr, radarr, etc.) - keep existing logic
        self._parse_services()
    
    def _parse_databases(self):
        """Parse all database backend configurations"""
        
        # Parse InfluxDB v1 (check both uppercase and lowercase for backward compatibility)
        if self.config.has_section('INFLUXDB') or self.config.has_section('influxdb'):
            influx_config = self._parse_influxdb_v1()
            if influx_config:
                self.database_configs.append(influx_config)
        
        # Parse InfluxDB v2
        if self.config.has_section('INFLUXDB2'):
            influx2_config = self._parse_influxdb_v2()
            if influx2_config:
                self.database_configs.append(influx2_config)
        
        # Parse InfluxDB v3
        if self.config.has_section('INFLUXDB3'):
            influx3_config = self._parse_influxdb_v3()
            if influx3_config:
                self.database_configs.append(influx3_config)
        
        # Parse TimescaleDB
        if self.config.has_section('TIMESCALEDB'):
            timescale_config = self._parse_timescaledb()
            if timescale_config:
                self.database_configs.append(timescale_config)
        
        # Parse QuestDB
        if self.config.has_section('QUESTDB'):
            questdb_config = self._parse_questdb()
            if questdb_config:
                self.database_configs.append(questdb_config)
        
        # Parse VictoriaMetrics
        if self.config.has_section('VICTORIAMETRICS'):
            victoriametrics_config = self._parse_victoriametrics()
            if victoriametrics_config:
                self.database_configs.append(victoriametrics_config)
    
    def _parse_influxdb_v1(self) -> DatabaseConfig:
        """Parse InfluxDB v1 configuration (supports both old and new format)"""
        # Check for uppercase first (new format), then lowercase (old format)
        section = 'INFLUXDB' if self.config.has_section('INFLUXDB') else 'influxdb'
        
        # Try to get hostname, fallback to 'url' for old configs
        hostname = self.config.get(section, 'hostname', fallback=None)
        if not hostname:
            hostname = self.config.get(section, 'url', fallback='localhost')
        
        # Try to get user, fallback to 'username' for old configs  
        username = self.config.get(section, 'user', fallback=None)
        if not username:
            username = self.config.get(section, 'username', fallback='')
        
        return DatabaseConfig(
            db_type='influxdb1',
            url=hostname,
            port=self.config.getint(section, 'port', fallback=8086),
            username=username,
            password=self.config.get(section, 'password', fallback=''),
            database=self.config.get(section, 'db', fallback='varken'),
            ssl=self.config.getboolean(section, 'ssl', fallback=False),
            verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=True),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _parse_influxdb_v2(self) -> DatabaseConfig:
        """Parse InfluxDB v2 configuration"""
        section = 'INFLUXDB2'
        return DatabaseConfig(
            db_type='influxdb2',
            url=self.config.get(section, 'hostname', fallback='localhost'),
            port=self.config.getint(section, 'port', fallback=8086),
            token=self.config.get(section, 'token', fallback=''),
            org=self.config.get(section, 'org', fallback=''),
            bucket=self.config.get(section, 'bucket', fallback='varken'),
            ssl=self.config.getboolean(section, 'ssl', fallback=False),
            verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=True),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _parse_influxdb_v3(self) -> DatabaseConfig:
        """Parse InfluxDB v3 configuration"""
        section = 'INFLUXDB3'
        return DatabaseConfig(
            db_type='influxdb3',
            url=self.config.get(section, 'hostname', fallback='localhost'),
            port=self.config.getint(section, 'port', fallback=443),
            token=self.config.get(section, 'token', fallback=''),
            org=self.config.get(section, 'org', fallback=''),
            bucket=self.config.get(section, 'bucket', fallback='varken'),
            database=self.config.get(section, 'database', fallback='varken'),
            ssl=self.config.getboolean(section, 'ssl', fallback=True),
            verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=True),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _parse_timescaledb(self) -> DatabaseConfig:
        """Parse TimescaleDB configuration"""
        section = 'TIMESCALEDB'
        return DatabaseConfig(
            db_type='timescale',
            url=self.config.get(section, 'hostname', fallback='localhost'),
            port=self.config.getint(section, 'port', fallback=5432),
            username=self.config.get(section, 'user', fallback='postgres'),
            password=self.config.get(section, 'password', fallback=''),
            database=self.config.get(section, 'database', fallback='varken'),
            ssl=self.config.getboolean(section, 'ssl', fallback=False),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _parse_questdb(self) -> DatabaseConfig:
        """Parse QuestDB configuration"""
        section = 'QUESTDB'
        return DatabaseConfig(
            db_type='questdb',
            url=self.config.get(section, 'hostname', fallback='localhost'),
            port=self.config.getint(section, 'port', fallback=9000),
            username=self.config.get(section, 'user', fallback=''),
            password=self.config.get(section, 'password', fallback=''),
            ssl=self.config.getboolean(section, 'ssl', fallback=False),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _parse_victoriametrics(self) -> DatabaseConfig:
        """Parse VictoriaMetrics configuration"""
        section = 'VICTORIAMETRICS'
        return DatabaseConfig(
            db_type='victoriametrics',
            url=self.config.get(section, 'hostname', fallback='localhost'),
            port=self.config.getint(section, 'port', fallback=8428),
            username=self.config.get(section, 'user', fallback=''),
            password=self.config.get(section, 'password', fallback=''),
            ssl=self.config.getboolean(section, 'ssl', fallback=False),
            verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=True),
            enabled=self.config.getboolean(section, 'enabled', fallback=True)
        )
    
    def _create_legacy_influx_server(self):
        """Create legacy InfluxServer object for backward compatibility"""
        # Find first InfluxDB v1 config
        influx_v1 = next((c for c in self.database_configs if c.db_type == 'influxdb1'), None)
        if influx_v1:
            return InfluxServer(
                url=influx_v1.url,
                port=influx_v1.port,
                username=influx_v1.username,
                password=influx_v1.password,
                ssl=influx_v1.ssl,
                verify_ssl=influx_v1.verify_ssl
            )
        return None
    
    def _parse_services(self):
        """Parse service configurations (sonarr, radarr, etc.)"""
        # Parse GLOBAL section for service IDs
        if self.config.has_section('global'):
            self.sonarr_server_ids = self._parse_server_ids('sonarr_server_ids')
            self.radarr_server_ids = self._parse_server_ids('radarr_server_ids')
            self.lidarr_server_ids = self._parse_server_ids('lidarr_server_ids')
            self.tautulli_server_ids = self._parse_server_ids('tautulli_server_ids')
            self.ombi_server_ids = self._parse_server_ids('ombi_server_ids')
            self.sickchill_server_ids = self._parse_server_ids('sickchill_server_ids')
            self.unifi_server_ids = self._parse_server_ids('unifi_server_ids')
        else:
            # Default to False if no global section
            self.sonarr_server_ids = False
            self.radarr_server_ids = False
            self.lidarr_server_ids = False
            self.tautulli_server_ids = False
            self.ombi_server_ids = False
            self.sickchill_server_ids = False
            self.unifi_server_ids = False
        
        # Set enabled flags based on server IDs
        self.sonarr_enabled = bool(self.sonarr_server_ids)
        self.radarr_enabled = bool(self.radarr_server_ids)
        self.lidarr_enabled = bool(self.lidarr_server_ids)
        self.tautulli_enabled = bool(self.tautulli_server_ids)
        self.ombi_enabled = bool(self.ombi_server_ids)
        self.sickchill_enabled = bool(self.sickchill_server_ids)
        self.unifi_enabled = bool(self.unifi_server_ids)
        
        # Parse MaxMind license key
        if self.config.has_section('global'):
            self.maxmind_license_key = self.config.get('global', 'maxmind_license_key', fallback=None)
        else:
            self.maxmind_license_key = None
        
        # Parse actual server configurations
        self.tautulli_servers = self._parse_tautulli_servers()
        self.sonarr_servers = self._parse_sonarr_servers()
        self.radarr_servers = self._parse_radarr_servers()
        self.lidarr_servers = self._parse_lidarr_servers()
        self.ombi_servers = self._parse_ombi_servers()
        self.sickchill_servers = self._parse_sickchill_servers()
        self.unifi_servers = self._parse_unifi_servers()
    
    def _parse_tautulli_servers(self) -> List[TautulliServer]:
        """Parse all Tautulli server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('tautulli-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(TautulliServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        fallback_ip=self.config.get(section, 'fallback_ip', fallback='1.1.1.1'),
                        api_key=self.config.get(section, 'apikey'),  # Read apikey, store as api_key
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        get_activity=self.config.getboolean(section, 'get_activity', fallback=True),
                        get_activity_run_seconds=self.config.getint(section, 'get_activity_run_seconds', fallback=30),
                        get_stats=self.config.getboolean(section, 'get_stats', fallback=True),
                        get_stats_run_seconds=self.config.getint(section, 'get_stats_run_seconds', fallback=3600),
                        maxmind_license_key=self.maxmind_license_key
                    ))
                except (ValueError, KeyError) as e:
                    pass
        return servers
    
    def _parse_sonarr_servers(self) -> List[SonarrServer]:
        """Parse all Sonarr server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('sonarr-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(SonarrServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        api_key=self.config.get(section, 'apikey'),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        missing_days=self.config.getint(section, 'missing_days', fallback=7),
                        missing_days_run_seconds=self.config.getint(section, 'missing_days_run_seconds', fallback=300),
                        future_days=self.config.getint(section, 'future_days', fallback=1),
                        future_days_run_seconds=self.config.getint(section, 'future_days_run_seconds', fallback=300),
                        queue=self.config.getboolean(section, 'queue', fallback=True),
                        queue_run_seconds=self.config.getint(section, 'queue_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_radarr_servers(self) -> List[RadarrServer]:
        """Parse all Radarr server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('radarr-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(RadarrServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        api_key=self.config.get(section, 'apikey'),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        queue=self.config.getboolean(section, 'queue', fallback=True),
                        queue_run_seconds=self.config.getint(section, 'queue_run_seconds', fallback=300),
                        get_missing=self.config.getboolean(section, 'get_missing', fallback=True),
                        get_missing_run_seconds=self.config.getint(section, 'get_missing_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_lidarr_servers(self) -> List[LidarrServer]:
        """Parse all Lidarr server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('lidarr-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(LidarrServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        api_key=self.config.get(section, 'apikey'),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        missing_days=self.config.getint(section, 'missing_days', fallback=30),
                        missing_days_run_seconds=self.config.getint(section, 'missing_days_run_seconds', fallback=300),
                        future_days=self.config.getint(section, 'future_days', fallback=30),
                        future_days_run_seconds=self.config.getint(section, 'future_days_run_seconds', fallback=300),
                        queue=self.config.getboolean(section, 'queue', fallback=True),
                        queue_run_seconds=self.config.getint(section, 'queue_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_ombi_servers(self) -> List[OmbiServer]:
        """Parse all Ombi server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('ombi-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(OmbiServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        api_key=self.config.get(section, 'apikey'),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        get_request_type_counts=self.config.getboolean(section, 'get_request_type_counts', fallback=True),
                        request_type_run_seconds=self.config.getint(section, 'request_type_run_seconds', fallback=300),
                        get_request_total_counts=self.config.getboolean(section, 'get_request_total_counts', fallback=True),
                        request_total_run_seconds=self.config.getint(section, 'request_total_run_seconds', fallback=300),
                        get_issue_status_counts=self.config.getboolean(section, 'get_issue_status_counts', fallback=True),
                        issue_status_run_seconds=self.config.getint(section, 'issue_status_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_sickchill_servers(self) -> List[SickChillServer]:
        """Parse all SickChill server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('sickchill-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(SickChillServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        api_key=self.config.get(section, 'apikey'),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        get_missing=self.config.getboolean(section, 'get_missing', fallback=True),
                        get_missing_run_seconds=self.config.getint(section, 'get_missing_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_unifi_servers(self) -> List[UniFiServer]:
        """Parse all UniFi server configurations"""
        servers = []
        for section in self.config.sections():
            if section.lower().startswith('unifi-'):
                try:
                    server_id = int(section.split('-')[1])
                    servers.append(UniFiServer(
                        id=server_id,
                        url=self.config.get(section, 'url'),
                        username=self.config.get(section, 'username'),
                        password=self.config.get(section, 'password'),
                        site=self.config.get(section, 'site', fallback='default'),
                        usg_name=self.config.get(section, 'usg_name', fallback=''),
                        ssl=self.config.getboolean(section, 'ssl', fallback=False),
                        verify_ssl=self.config.getboolean(section, 'verify_ssl', fallback=False),
                        get_usg_stats_run_seconds=self.config.getint(section, 'get_usg_stats_run_seconds', fallback=300)
                    ))
                except (ValueError, KeyError):
                    pass
        return servers
    
    def _parse_server_ids(self, key):
        """Parse server IDs from global section"""
        if not self.config.has_section('global'):
            return False
        
        value = self.config.get('global', key, fallback='false')
        
        # Handle boolean false
        if value.lower() in ('false', 'no', '0', ''):
            return False
        
        # Handle boolean true (treated as empty list or default)
        if value.lower() in ('true', 'yes', '1'):
            return True
        
        # Handle comma-separated list of IDs
        try:
            ids = [int(x.strip()) for x in value.split(',') if x.strip()]
            return ids if ids else False
        except ValueError:
            # If parsing fails, return the raw value
            return value
    
    def get_database_configs(self) -> List[DatabaseConfig]:
        """Get all configured database backends"""
        return self.database_configs
    
    def get_enabled_databases(self) -> List[DatabaseConfig]:
        """Get only enabled database backends"""
        return [c for c in self.database_configs if c.enabled]
