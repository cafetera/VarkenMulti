"""
Enhanced DBManager for Varken with Multi-Database Backend Support
Supports: InfluxDB v1.x, v2.x, v3.x, TimescaleDB, QuestDB, VictoriaMetrics
Includes multi-database fan-out capability
"""

from logging import getLogger
from influxdb import InfluxDBClient as InfluxDBClient_v1
from influxdb_client import InfluxDBClient as InfluxDBClient_v2
from influxdb_client.client.write_api import SYNCHRONOUS
import psycopg2
from psycopg2.extras import execute_batch
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json


def normalize_data_types(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize data types to prevent field type conflicts
    
    Common issues:
    - progress_percent can be float or int -> always make int
    - Numeric strings -> convert to proper types
    - None values -> remove field
    """
    normalized = []
    
    for point in points:
        normalized_point = {
            'measurement': point.get('measurement'),
            'tags': point.get('tags', {}).copy(),
            'fields': {},
            'time': point.get('time')
        }
        
        # Normalize fields
        for key, value in point.get('fields', {}).items():
            # Skip None values
            if value is None:
                continue
            
            # Normalize specific fields known to cause type conflicts
            if key == 'progress_percent':
                # Always make this an integer
                try:
                    normalized_point['fields'][key] = int(float(value))
                except (ValueError, TypeError):
                    continue  # Skip if can't convert
            elif key in ['season', 'episode', 'media_index', 'parent_media_index']:
                # Always integers
                try:
                    normalized_point['fields'][key] = int(value)
                except (ValueError, TypeError):
                    continue
            else:
                # Keep as-is
                normalized_point['fields'][key] = value
        
        # Only add if we have fields
        if normalized_point['fields']:
            normalized.append(normalized_point)
    
    return normalized


@dataclass
class DatabaseConfig:
    """Configuration for a database backend"""
    db_type: str  # 'influxdb1', 'influxdb2', 'influxdb3', 'timescale', 'questdb', 'victoriametrics'
    url: str
    port: int
    database: str = 'varken'
    # InfluxDB specific
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    org: Optional[str] = None
    bucket: Optional[str] = None
    # SSL/TLS
    ssl: bool = False
    verify_ssl: bool = True
    # Connection settings
    timeout: int = 10
    enabled: bool = True


class DatabaseBackend(ABC):
    """Abstract base class for database backends"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = getLogger()
        self.client = None
        
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to database"""
        pass
    
    @abstractmethod
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        """Write data points to database"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test database connection"""
        pass
    
    @abstractmethod
    def close(self):
        """Close database connection"""
        pass


class InfluxDBv1Backend(DatabaseBackend):
    """InfluxDB 1.x backend"""
    
    def connect(self) -> bool:
        try:
            self.client = InfluxDBClient_v1(
                host=self.config.url,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
                ssl=self.config.ssl,
                database=self.config.database,
                verify_ssl=self.config.verify_ssl,
                timeout=self.config.timeout
            )
            return self.test_connection()
        except Exception as e:
            self.logger.error(f"InfluxDB v1 connection error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            version = self.client.request('ping', expected_response_code=204).headers.get('X-Influxdb-Version')
            self.logger.info(f'InfluxDB v1 version: {version}')
            
            # Check if database exists, create if not
            databases = [db['name'] for db in self.client.get_list_database()]
            if self.config.database not in databases:
                self.client.create_database(self.config.database)
                self.logger.info(f"Created database: {self.config.database}")
                
                # Create retention policy
                self.client.create_retention_policy(
                    name='varken 30d-1h',
                    duration='30d',
                    replication='1',
                    database=self.config.database,
                    default=True,
                    shard_duration='1h'
                )
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB v1 test connection failed: {e}")
            return False
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        try:
            return self.client.write_points(points)
        except Exception as e:
            self.logger.error(f"InfluxDB v1 write error: {e}")
            return False
    
    def close(self):
        if self.client:
            self.client.close()


class InfluxDBv2Backend(DatabaseBackend):
    """InfluxDB 2.x backend"""
    
    def connect(self) -> bool:
        try:
            url = f"{'https' if self.config.ssl else 'http'}://{self.config.url}:{self.config.port}"
            self.client = InfluxDBClient_v2(
                url=url,
                token=self.config.token,
                org=self.config.org,
                timeout=self.config.timeout * 1000,
                verify_ssl=self.config.verify_ssl
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            return self.test_connection()
        except Exception as e:
            self.logger.error(f"InfluxDB v2 connection error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            health = self.client.health()
            self.logger.info(f'InfluxDB v2 status: {health.status}, version: {health.version}')
            
            # Check if bucket exists
            buckets_api = self.client.buckets_api()
            bucket = buckets_api.find_bucket_by_name(self.config.bucket)
            if not bucket:
                self.logger.warning(f"Bucket '{self.config.bucket}' not found. Please create it manually.")
            
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB v2 test connection failed: {e}")
            return False
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        try:
            # Convert InfluxDB v1 format to v2 line protocol
            lines = []
            for point in points:
                line = self._format_line_protocol(point)
                if line:
                    lines.append(line)
            
            if lines:
                # Write all lines at once
                self.write_api.write(bucket=self.config.bucket, org=self.config.org, record=lines)
            
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB v2 write error: {e}")
            return False
    
    def _format_line_protocol(self, point: Dict[str, Any]) -> str:
        """Format a point as InfluxDB line protocol"""
        measurement = point.get('measurement')
        tags = point.get('tags', {})
        fields = point.get('fields', {})
        time = point.get('time')
        
        if not measurement or not fields:
            return None
        
        # Escape measurement
        measurement = measurement.replace(',', '\\,').replace(' ', '\\ ')
        
        # Build tag set
        tag_parts = []
        for k, v in sorted(tags.items()):
            if v is not None and v != '':
                k = str(k).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
                v = str(v).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
                tag_parts.append(f"{k}={v}")
        
        # Build field set with proper typing
        field_parts = []
        for k, v in fields.items():
            if v is None:
                continue
            
            k = str(k).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
            
            # Format value based on type
            if isinstance(v, bool):
                v_str = 'true' if v else 'false'
            elif isinstance(v, int):
                v_str = f"{v}i"  # Integer with 'i' suffix
            elif isinstance(v, float):
                v_str = str(v)  # Float
            else:
                # String - needs quotes and escaping
                v_escaped = str(v).replace('\\', '\\\\').replace('"', '\\"')
                v_str = f'"{v_escaped}"'
            
            field_parts.append(f"{k}={v_str}")
        
        if not field_parts:
            return None
        
        # Build the line
        line = measurement
        if tag_parts:
            line += ',' + ','.join(tag_parts)
        line += ' ' + ','.join(field_parts)
        
        # Add timestamp if present - convert to nanoseconds
        if time:
            if isinstance(time, str):
                # ISO 8601 format - convert to nanoseconds
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
                    timestamp_ns = int(dt.timestamp() * 1_000_000_000)
                    line += f" {timestamp_ns}"
                except:
                    pass  # Skip timestamp if parsing fails
            elif isinstance(time, int):
                line += f" {time}"
        
        return line
    
    def close(self):
        if self.client:
            self.client.close()


class InfluxDBv3Backend(DatabaseBackend):
    """InfluxDB 3.x backend (Cloud/Core)"""
    
    def connect(self) -> bool:
        try:
            # InfluxDB v3 uses v2 client but with different API structure
            url = f"{'https' if self.config.ssl else 'http'}://{self.config.url}:{self.config.port}"
            self.client = InfluxDBClient_v2(
                url=url,
                token=self.config.token,
                org=self.config.org,
                timeout=self.config.timeout * 1000,
                verify_ssl=self.config.verify_ssl
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            return self.test_connection()
        except Exception as e:
            self.logger.error(f"InfluxDB v3 connection error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            # InfluxDB v3 health check
            health = self.client.health()
            self.logger.info(f'InfluxDB v3 status: {health.status}')
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB v3 test connection failed: {e}")
            return False
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        # Same formatting as v2
        try:
            lines = []
            for point in points:
                line = self._format_line_protocol(point)
                if line:
                    lines.append(line)
            
            if lines:
                self.write_api.write(bucket=self.config.bucket, org=self.config.org, record=lines)
            
            return True
        except Exception as e:
            self.logger.error(f"InfluxDB v3 write error: {e}")
            return False
    
    def _format_line_protocol(self, point: Dict[str, Any]) -> str:
        """Format a point as InfluxDB line protocol (same as v2)"""
        measurement = point.get('measurement')
        tags = point.get('tags', {})
        fields = point.get('fields', {})
        time = point.get('time')
        
        if not measurement or not fields:
            return None
        
        # Escape measurement
        measurement = measurement.replace(',', '\\,').replace(' ', '\\ ')
        
        # Build tag set
        tag_parts = []
        for k, v in sorted(tags.items()):
            if v is not None and v != '':
                k = str(k).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
                v = str(v).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
                tag_parts.append(f"{k}={v}")
        
        # Build field set with proper typing
        field_parts = []
        for k, v in fields.items():
            if v is None:
                continue
            
            k = str(k).replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
            
            # Format value based on type
            if isinstance(v, bool):
                v_str = 'true' if v else 'false'
            elif isinstance(v, int):
                v_str = f"{v}i"  # Integer with 'i' suffix
            elif isinstance(v, float):
                v_str = str(v)  # Float
            else:
                # String - needs quotes and escaping
                v_escaped = str(v).replace('\\', '\\\\').replace('"', '\\"')
                v_str = f'"{v_escaped}"'
            
            field_parts.append(f"{k}={v_str}")
        
        if not field_parts:
            return None
        
        # Build the line
        line = measurement
        if tag_parts:
            line += ',' + ','.join(tag_parts)
        line += ' ' + ','.join(field_parts)
        
        # Add timestamp if present - convert to nanoseconds
        if time:
            if isinstance(time, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
                    timestamp_ns = int(dt.timestamp() * 1_000_000_000)
                    line += f" {timestamp_ns}"
                except:
                    pass
            elif isinstance(time, int):
                line += f" {time}"
        
        return line
    
    def close(self):
        if self.client:
            self.client.close()


class TimescaleDBBackend(DatabaseBackend):
    """TimescaleDB backend with proper column-based schema"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.connection = None
        self.cursor = None
        self.known_columns = set()  # Cache of existing columns
    
    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(
                host=self.config.url,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                connect_timeout=self.config.timeout,
                sslmode='require' if self.config.ssl else 'prefer',
                client_encoding='UTF8'  # Force UTF-8 encoding
            )
            self.connection.set_client_encoding('UTF8')
            self.cursor = self.connection.cursor()
            return self.test_connection()
        except Exception as e:
            self.logger.error(f"TimescaleDB connection error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()[0]
            self.logger.info(f'TimescaleDB version: {version}')
            
            # Check if TimescaleDB extension is enabled
            self.cursor.execute("SELECT * FROM pg_extension WHERE extname = 'timescaledb';")
            if not self.cursor.fetchone():
                self.logger.warning("TimescaleDB extension not found. Creating...")
                self.cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                self.connection.commit()
            
            # Create base table structure
            self._create_tables()
            return True
        except Exception as e:
            self.logger.error(f"TimescaleDB test connection failed: {e}")
            return False
    
    def _create_tables(self):
        """Create hypertables with base columns"""
        # Create table with time column
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS varken_metrics (
                time TIMESTAMPTZ NOT NULL
            );
        """)
        
        # Convert to hypertable if not already
        try:
            self.cursor.execute("""
                SELECT create_hypertable('varken_metrics', 'time', 
                                        if_not_exists => TRUE,
                                        migrate_data => TRUE);
            """)
        except Exception as e:
            # Table might already be a hypertable
            self.logger.debug(f"Hypertable creation: {e}")
        
        self.connection.commit()
        
        # Load existing columns into cache
        self._load_existing_columns()
        
        self.logger.info("TimescaleDB base table created/verified")
    
    def _load_existing_columns(self):
        """Load existing columns from the database into cache"""
        self.cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'varken_metrics';
        """)
        self.known_columns = {row[0] for row in self.cursor.fetchall()}
        self.logger.debug(f"Loaded {len(self.known_columns)} existing columns")
    
    def _ensure_column_exists(self, column_name: str, column_type: str):
        """Add column if it doesn't exist (with timeout protection)"""
        # Sanitize column name (lowercase, replace spaces with underscores)
        safe_column = column_name.lower().replace(' ', '_').replace('-', '_')
        
        # Skip if already exists
        if safe_column in self.known_columns:
            return safe_column
        
        try:
            # Determine PostgreSQL type
            if column_type == 'int':
                pg_type = 'BIGINT'
            elif column_type == 'float':
                pg_type = 'DOUBLE PRECISION'
            elif column_type == 'bool':
                pg_type = 'BOOLEAN'
            else:
                pg_type = 'TEXT'
            
            # Set statement timeout to prevent hanging (5 seconds)
            self.cursor.execute("SET statement_timeout = '5s';")
            
            # Add column
            self.cursor.execute(f"""
                ALTER TABLE varken_metrics 
                ADD COLUMN IF NOT EXISTS {safe_column} {pg_type};
            """)
            self.connection.commit()
            
            # Reset timeout
            self.cursor.execute("SET statement_timeout = 0;")
            
            # Add to cache
            self.known_columns.add(safe_column)
            self.logger.debug(f"Added column: {safe_column} ({pg_type})")
            
        except Exception as e:
            self.logger.warning(f"Could not add column {safe_column}: {e}")
            self.connection.rollback()
            # Reset timeout
            try:
                self.cursor.execute("SET statement_timeout = 0;")
            except:
                pass
        
        return safe_column
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        try:
            for point in points:
                time = point.get('time')
                tags = point.get('tags', {})
                fields = point.get('fields', {})
                
                # Prepare column names and values
                columns = ['time']
                values = []
                placeholders = ['%s']
                
                # Convert timestamp
                if isinstance(time, str):
                    from datetime import datetime
                    try:
                        dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
                        values.append(dt)
                    except:
                        from datetime import datetime
                        values.append(datetime.now())
                else:
                    from datetime import datetime
                    values.append(datetime.now())
                
                # Process tags (these become columns)
                for tag_key, tag_value in tags.items():
                    if tag_value is not None:
                        col_name = self._ensure_column_exists(tag_key, 'text')
                        columns.append(col_name)
                        # Ensure proper Unicode string encoding
                        if isinstance(tag_value, bytes):
                            tag_value = tag_value.decode('utf-8', errors='replace')
                        values.append(str(tag_value))
                        placeholders.append('%s')
                
                # Process fields (these become columns with proper types)
                for field_key, field_value in fields.items():
                    if field_value is None:
                        continue
                    
                    # Determine type
                    if isinstance(field_value, bool):
                        col_type = 'bool'
                    elif isinstance(field_value, int):
                        col_type = 'int'
                    elif isinstance(field_value, float):
                        col_type = 'float'
                    else:
                        col_type = 'text'
                        # Ensure proper Unicode string encoding for text fields
                        if isinstance(field_value, bytes):
                            field_value = field_value.decode('utf-8', errors='replace')
                        elif not isinstance(field_value, str):
                            field_value = str(field_value)
                    
                    col_name = self._ensure_column_exists(field_key, col_type)
                    columns.append(col_name)
                    values.append(field_value)
                    placeholders.append('%s')
                
                # Insert data
                query = f"""
                    INSERT INTO varken_metrics ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                
                self.cursor.execute(query, values)
            
            self.connection.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"TimescaleDB write error: {e}")
            self.connection.rollback()
            return False
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()



class QuestDBBackend(DatabaseBackend):
    """QuestDB backend using InfluxDB Line Protocol over HTTP"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.base_url = f"{'https' if config.ssl else 'http'}://{config.url}:{config.port}"
        self.session = requests.Session()
        if config.username and config.password:
            self.session.auth = (config.username, config.password)
    
    def connect(self) -> bool:
        return self.test_connection()
    
    def test_connection(self) -> bool:
        try:
            # Test connection to QuestDB - try the exec endpoint which is more reliable
            response = self.session.get(
                f"{self.base_url}/exec",
                params={'query': 'SELECT 1'},
                timeout=self.config.timeout,
                allow_redirects=True
            )
            if response.status_code == 200:
                self.logger.info('QuestDB connection successful')
                return True
            else:
                self.logger.error(f"QuestDB connection failed with status: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"QuestDB test connection failed: {e}")
            return False
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        try:
            # Convert to InfluxDB Line Protocol
            lines = []
            for point in points:
                measurement = point.get('measurement')
                tags = point.get('tags', {})
                fields = point.get('fields', {})
                time = point.get('time')
                
                if not measurement or not fields:
                    continue  # Skip invalid points
                
                # Escape measurement name
                measurement = self._escape_measurement(measurement)
                
                # Build tag set
                tag_parts = []
                for k, v in sorted(tags.items()):  # Sort for consistency
                    if v is not None and v != '':
                        k = self._escape_tag_key(str(k))
                        v = self._escape_tag_value(str(v))
                        tag_parts.append(f"{k}={v}")
                
                # Build field set
                field_parts = []
                for k, v in fields.items():
                    if v is None:
                        continue
                    
                    k = self._escape_field_key(str(k))
                    
                    # Format field value based on type
                    if isinstance(v, bool):
                        v_str = 'true' if v else 'false'
                    elif isinstance(v, int):
                        v_str = f"{v}i"  # Integer
                    elif isinstance(v, float):
                        v_str = str(v)  # Float
                    else:
                        # String - needs quotes and escaping
                        v_str = f'"{self._escape_field_string_value(str(v))}"'
                    
                    field_parts.append(f"{k}={v_str}")
                
                if not field_parts:
                    continue  # Skip if no valid fields
                
                # Build the line
                line = measurement
                if tag_parts:
                    line += ',' + ','.join(tag_parts)
                line += ' ' + ','.join(field_parts)
                if time:
                    # Convert timestamp to nanoseconds if needed
                    line += f" {self._convert_timestamp(time)}"
                
                lines.append(line)
            
            if not lines:
                return True  # Nothing to write
            
            # Send to QuestDB via HTTP
            data = '\n'.join(lines)
            
            response = self.session.post(
                f"{self.base_url}/write?db=varken",
                data=data,
                timeout=self.config.timeout,
                headers={'Content-Type': 'text/plain'}
            )
            
            if response.status_code in [200, 204]:
                return True
            else:
                self.logger.error(f"QuestDB write failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"QuestDB write error: {e}")
            return False
    
    def _escape_measurement(self, s: str) -> str:
        """Escape measurement name"""
        return s.replace(',', '\\,').replace(' ', '\\ ')
    
    def _escape_tag_key(self, s: str) -> str:
        """Escape tag key"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_tag_value(self, s: str) -> str:
        """Escape tag value"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_field_key(self, s: str) -> str:
        """Escape field key"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_field_string_value(self, s: str) -> str:
        """Escape string field value (used inside quotes)"""
        return s.replace('\\', '\\\\').replace('"', '\\"')  # Backslash FIRST!
    
    def _convert_timestamp(self, ts) -> str:
        """Convert timestamp to nanoseconds for QuestDB"""
        if isinstance(ts, int):
            # Already a timestamp, assume it's in nanoseconds
            return str(ts)
        elif isinstance(ts, str):
            # ISO 8601 format: 2026-01-09T15:03:18.844999+00:00
            try:
                from datetime import datetime
                # Parse ISO format
                dt = datetime.fromisoformat(ts.replace('+00:00', '+00:00'))
                # Convert to nanoseconds since epoch
                timestamp_ns = int(dt.timestamp() * 1_000_000_000)
                return str(timestamp_ns)
            except Exception as e:
                self.logger.warning(f"Could not parse timestamp '{ts}': {e}")
                # Return current time in nanoseconds
                from time import time_ns
                return str(time_ns())
        else:
            # Unknown format, use current time
            from time import time_ns
            return str(time_ns())
    
    def close(self):
        if self.session:
            self.session.close()


class VictoriaMetricsBackend(DatabaseBackend):
    """VictoriaMetrics backend using InfluxDB Line Protocol"""
    
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self.base_url = f"{'https' if config.ssl else 'http'}://{config.url}:{config.port}"
        self.session = requests.Session()
        if config.username and config.password:
            self.session.auth = (config.username, config.password)
    
    def connect(self) -> bool:
        return self.test_connection()
    
    def test_connection(self) -> bool:
        try:
            # Test connection to VictoriaMetrics
            # VictoriaMetrics doesn't have a dedicated health endpoint like InfluxDB
            # We can test the write endpoint with a simple query
            response = self.session.get(
                f"{self.base_url}/api/v1/labels",
                timeout=self.config.timeout,
                allow_redirects=True
            )
            if response.status_code == 200:
                self.logger.info('VictoriaMetrics connection successful')
                return True
            else:
                self.logger.error(f"VictoriaMetrics connection failed with status: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"VictoriaMetrics test connection failed: {e}")
            return False
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        try:
            # Convert to InfluxDB Line Protocol
            lines = []
            for point in points:
                measurement = point.get('measurement')
                tags = point.get('tags', {})
                fields = point.get('fields', {})
                time = point.get('time')
                
                if not measurement or not fields:
                    continue  # Skip invalid points
                
                # Escape measurement name
                measurement = self._escape_measurement(measurement)
                
                # Build tag set
                tag_parts = []
                for k, v in sorted(tags.items()):  # Sort for consistency
                    if v is not None and v != '':
                        k = self._escape_tag_key(str(k))
                        v = self._escape_tag_value(str(v))
                        tag_parts.append(f"{k}={v}")
                
                # Build field set
                field_parts = []
                for k, v in fields.items():
                    if v is None:
                        continue
                    
                    k = self._escape_field_key(str(k))
                    
                    # Format field value based on type
                    if isinstance(v, bool):
                        v_str = 'true' if v else 'false'
                    elif isinstance(v, int):
                        v_str = f"{v}i"  # Integer
                    elif isinstance(v, float):
                        v_str = str(v)  # Float
                    else:
                        # String - needs quotes and escaping
                        v_str = f'"{self._escape_field_string_value(str(v))}"'
                    
                    field_parts.append(f"{k}={v_str}")
                
                if not field_parts:
                    continue  # Skip if no valid fields
                
                # Build the line
                line = measurement
                if tag_parts:
                    line += ',' + ','.join(tag_parts)
                line += ' ' + ','.join(field_parts)
                if time:
                    # Convert timestamp to nanoseconds if needed
                    line += f" {self._convert_timestamp(time)}"
                
                lines.append(line)
            
            if not lines:
                return True  # Nothing to write
            
            # Send to VictoriaMetrics via HTTP
            # VictoriaMetrics supports InfluxDB line protocol via /write endpoint
            data = '\n'.join(lines)
            response = self.session.post(
                f"{self.base_url}/write?db=varken",
                data=data,
                timeout=self.config.timeout,
                headers={'Content-Type': 'text/plain'}
            )
            
            if response.status_code in [200, 204]:
                return True
            else:
                self.logger.error(f"VictoriaMetrics write failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"VictoriaMetrics write error: {e}")
            return False
    
    def _escape_measurement(self, s: str) -> str:
        """Escape measurement name"""
        return s.replace(',', '\\,').replace(' ', '\\ ')
    
    def _escape_tag_key(self, s: str) -> str:
        """Escape tag key"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_tag_value(self, s: str) -> str:
        """Escape tag value"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_field_key(self, s: str) -> str:
        """Escape field key"""
        return s.replace(',', '\\,').replace('=', '\\=').replace(' ', '\\ ')
    
    def _escape_field_string_value(self, s: str) -> str:
        """Escape string field value (used inside quotes)"""
        return s.replace('\\', '\\\\').replace('"', '\\"')  # Backslash FIRST!
    
    def _convert_timestamp(self, ts) -> str:
        """Convert timestamp to nanoseconds for VictoriaMetrics"""
        if isinstance(ts, int):
            # Already a timestamp, assume it's in nanoseconds
            return str(ts)
        elif isinstance(ts, str):
            # ISO 8601 format: 2026-01-09T15:03:18.844999+00:00
            try:
                from datetime import datetime
                # Parse ISO format
                dt = datetime.fromisoformat(ts.replace('+00:00', '+00:00'))
                # Convert to nanoseconds since epoch
                timestamp_ns = int(dt.timestamp() * 1_000_000_000)
                return str(timestamp_ns)
            except Exception as e:
                self.logger.warning(f"Could not parse timestamp '{ts}': {e}")
                # Return current time in nanoseconds
                from time import time_ns
                return str(time_ns())
        else:
            # Unknown format, use current time
            from time import time_ns
            return str(time_ns())
    
    def close(self):
        if self.session:
            self.session.close()


class MultiDBManager:
    """
    Enhanced Database Manager with Multi-Backend Support
    Handles writing to multiple databases simultaneously
    """
    
    def __init__(self, configs: List[DatabaseConfig]):
        self.logger = getLogger()
        self.backends: List[DatabaseBackend] = []
        
        # Initialize all configured backends
        for config in configs:
            if not config.enabled:
                continue
            
            try:
                backend = self._create_backend(config)
                if backend.connect():
                    self.backends.append(backend)
                    self.logger.info(f"Successfully connected to {config.db_type} at {config.url}:{config.port}")
                else:
                    self.logger.error(f"Failed to connect to {config.db_type} at {config.url}:{config.port}")
            except Exception as e:
                self.logger.error(f"Error initializing {config.db_type}: {e}")
        
        if not self.backends:
            self.logger.critical("No database backends successfully initialized!")
            raise Exception("No database backends available")
    
    def _create_backend(self, config: DatabaseConfig) -> DatabaseBackend:
        """Factory method to create appropriate backend"""
        backend_map = {
            'influxdb1': InfluxDBv1Backend,
            'influxdb2': InfluxDBv2Backend,
            'influxdb3': InfluxDBv3Backend,
            'timescale': TimescaleDBBackend,
            'questdb': QuestDBBackend,
            'victoriametrics': VictoriaMetricsBackend
        }
        
        backend_class = backend_map.get(config.db_type.lower())
        if not backend_class:
            raise ValueError(f"Unknown database type: {config.db_type}")
        
        return backend_class(config)
    
    def write_points(self, points: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        Write points to all configured backends with timeout protection
        Returns dict with status for each backend
        """
        import threading
        
        # Normalize data types before writing to prevent type conflicts
        normalized_points = normalize_data_types(points)
        
        if not normalized_points:
            self.logger.warning("No valid points after normalization")
            return {}
        
        results = {}
        
        def write_with_timeout(backend, points, timeout=30):
            """Write to backend with timeout"""
            result = {'success': False, 'error': None}
            
            def do_write():
                try:
                    result['success'] = backend.write_points(points)
                except Exception as e:
                    result['error'] = str(e)
            
            thread = threading.Thread(target=do_write)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                result['error'] = f"Write timeout after {timeout}s"
                result['success'] = False
            
            return result['success'], result['error']
        
        for backend in self.backends:
            db_name = f"{backend.config.db_type}@{backend.config.url}:{backend.config.port}"
            try:
                # Use timeout for write
                success, error = write_with_timeout(backend, normalized_points, timeout=30)
                results[db_name] = success
                
                if not success:
                    if error:
                        self.logger.warning(f"Failed to write to {db_name}: {error}")
                    else:
                        self.logger.warning(f"Failed to write to {db_name}")
                        
            except Exception as e:
                self.logger.error(f"Error writing to {db_name}: {e}")
                results[db_name] = False
        
        return results
    
    def close_all(self):
        """Close all database connections"""
        for backend in self.backends:
            try:
                backend.close()
            except Exception as e:
                self.logger.error(f"Error closing {backend.config.db_type}: {e}")
    
    def get_backend_count(self) -> int:
        """Get number of active backends"""
        return len(self.backends)
    
    def get_backend_info(self) -> List[Dict[str, Any]]:
        """Get information about all backends"""
        return [
            {
                'type': backend.config.db_type,
                'url': backend.config.url,
                'port': backend.config.port,
                'database': backend.config.database,
                'enabled': backend.config.enabled
            }
            for backend in self.backends
        ]


# Legacy compatibility wrapper
class DBManager:
    """
    Legacy DBManager interface for backward compatibility
    Wraps MultiDBManager to maintain existing API
    """
    
    def __init__(self, server_config):
        """
        Initialize with legacy server config or new multi-config
        """
        self.logger = getLogger()
        
        # Check if this is legacy single config or new multi config
        if isinstance(server_config, list):
            # New multi-database configuration
            self.multi_manager = MultiDBManager(server_config)
        else:
            # Legacy single InfluxDB v1 configuration
            config = DatabaseConfig(
                db_type='influxdb1',
                url=server_config.url,
                port=server_config.port,
                username=server_config.username,
                password=server_config.password,
                ssl=server_config.ssl,
                verify_ssl=server_config.verify_ssl,
                database='varken'
            )
            self.multi_manager = MultiDBManager([config])
        
        # Store reference to primary backend for legacy compatibility
        self.influx = self.multi_manager.backends[0].client if self.multi_manager.backends else None
    
    def write_points(self, points: List[Dict[str, Any]]) -> bool:
        """Write points to all configured databases"""
        results = self.multi_manager.write_points(points)
        # Return True if at least one backend succeeded
        return any(results.values())
    
    def close(self):
        """Close all database connections"""
        self.multi_manager.close_all()
