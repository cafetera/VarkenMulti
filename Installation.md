# Varken Multi-Database - Complete Installation Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start (15 Minutes)](#quick-start-15-minutes)
4. [Detailed Installation](#detailed-installation)
5. [Database Setup](#database-setup)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Grafana Integration](#grafana-integration)
9. [Troubleshooting](#troubleshooting)
10. [Upgrading from Original Varken](#upgrading-from-original-varken)

---

## Overview

This guide will help you install Varken with multi-database support, enabling you to write metrics to:

- ✅ InfluxDB v1.x, v2.x, v3.x
- ✅ TimescaleDB (PostgreSQL extension)
- ✅ QuestDB
- ✅ VictoriaMetrics

**Write to multiple databases simultaneously for redundancy, testing, or migration!**

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, or similar)
- **RAM**: 512MB minimum, 1GB recommended
- **Disk**: 500MB for Varken, plus database storage
- **CPU**: 1 core minimum, 2+ cores recommended

### Required Software

- **Python**: 3.8 or higher
- **pip**: Python package manager
- **systemd**: For service management (usually pre-installed)

### Optional (For Databases)

- **Docker**: If using containerized databases
- **PostgreSQL**: For TimescaleDB
- **VictoriaMetrics
- **QuestDB
- **InfluxDB**: Your choice of v1, v2, or v3

### Services You'll Monitor

At least one of:
- Tautulli (Plex monitoring)
- Sonarr (TV shows)
- Radarr (Movies)
- Lidarr (Music)
- Ombi (Requests)
- SickChill
- UniFi Controller

---

## Quick Start (15 Minutes)

For experienced users who want to get running quickly:

```bash
# 1. Install Varken
cd /opt
sudo git clone https://github.com/Boerderij/Varken
cd Varken
sudo pip3 install -r requirements.txt --break-system-packages

# 2. Install enhanced multi-database files
sudo cp /path/to/dbmanager_v2_questdb_fixed.py /opt/Varken/varken/dbmanager_v2.py
sudo cp /path/to/iniparser_v2_complete.py /opt/Varken/varken/iniparser_v2.py

# 3. Install enhanced dependencies
sudo pip3 install influxdb-client psycopg2-binary --break-system-packages

# 4. Configure
sudo cp /opt/Varken/data/varken.example.ini /opt/Varken/data/varken.ini
sudo nano /opt/Varken/data/varken.ini  # Edit configuration

# 5. Setup systemd service
sudo cp varken.service /etc/systemd/system/varken.service
sudo systemctl daemon-reload
sudo systemctl enable varken
sudo systemctl start varken

# 6. Verify
sudo journalctl -u varken -n 50
```

**Done!** Skip to [Verification](#verification)

---

## Detailed Installation

### Step 1: Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip git curl
```

#### CentOS/RHEL
```bash
sudo yum install -y python3 python3-pip git curl
```

#### Verify Installation
```bash
python3 --version  # Should be 3.8 or higher
pip3 --version
```

### Step 2: Create Varken User (Recommended)

Running Varken as a dedicated user improves security:

```bash
# Create varken user
sudo useradd -r -s /bin/false varken

# Create directories
sudo mkdir -p /opt/Varken
sudo chown varken:varken /opt/Varken
```

### Step 3: Download Varken

#### Option A: From GitHub (Original)
```bash
cd /opt
sudo git clone https://github.com/Boerderij/Varken
cd Varken
```

#### Option B: From Release Package
```bash
cd /opt
sudo wget https://github.com/Boerderij/Varken/archive/refs/heads/develop.zip
sudo unzip develop.zip
sudo mv Varken-develop Varken
cd Varken
```

### Step 4: Install Python Dependencies

#### Install Base Dependencies
```bash
cd /opt/Varken
sudo pip3 install -r requirements.txt --break-system-packages
```

**Note**: The `--break-system-packages` flag is needed on newer systems (Debian 12+, Ubuntu 23.04+) that use externally-managed Python.

#### Install Enhanced Database Dependencies
```bash
sudo pip3 install influxdb-client psycopg2-binary --break-system-packages
```

**Dependencies installed:**
- `influxdb` - InfluxDB v1 client
- `influxdb-client` - InfluxDB v2/v3 client
- `psycopg2-binary` - PostgreSQL/TimescaleDB client
- `requests` - HTTP client (for QuestDB, VictoriaMetrics)

### Step 5: Install Multi-Database Enhancement

Copy the enhanced files:

```bash
# Copy database manager
sudo cp /path/to/dbmanager_v2_questdb_fixed.py /opt/Varken/varken/dbmanager_v2.py

# Copy configuration parser
sudo cp /path/to/iniparser_v2_complete.py /opt/Varken/varken/iniparser_v2.py

# Set permissions
sudo chown varken:varken /opt/Varken/varken/dbmanager_v2.py
sudo chown varken:varken /opt/Varken/varken/iniparser_v2.py
```

### Step 6: Update Varken.py

Edit `/opt/Varken/Varken.py` to use the enhanced parser:

```bash
sudo nano /opt/Varken/Varken.py
```

Find this line (around line 25):
```python
from varken.iniparser import INIParser
```

Change to:
```python
from varken.iniparser_v2 import EnhancedINIParser as INIParser
```

Find this line (around line 27):
```python
from varken.dbmanager import DBManager
```

Change to:
```python
from varken.dbmanager_v2 import DBManager
```

Find this section (around line 100-120):
```python
DBMANAGER = DBManager(CONFIG.influx_server)
```

Replace with:
```python
# Initialize database manager with enhanced multi-database support
if hasattr(CONFIG, 'get_enabled_databases'):
    enabled_dbs = CONFIG.get_enabled_databases()
    
    if not enabled_dbs:
        logger.critical("No enabled databases found in config!")
        logger.critical("Please set 'enabled = true' for at least one database section")
        sys.exit(1)
    
    logger.info(f"Found {len(enabled_dbs)} enabled database(s)")
    DBMANAGER = DBManager(enabled_dbs)
    logger.info(f"✓ Database manager initialized with {len(enabled_dbs)} backend(s)")
else:
    # Fallback to legacy
    DBMANAGER = DBManager(CONFIG.influx_server)
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

---

## Database Setup

You need at least **one** database. Here's how to set up each:

### Option 1: InfluxDB v1 (Easiest)

#### Install InfluxDB v1
```bash
# Ubuntu/Debian
wget https://dl.influxdata.com/influxdb/releases/influxdb_1.8.10_amd64.deb
sudo dpkg -i influxdb_1.8.10_amd64.deb
sudo systemctl enable influxdb
sudo systemctl start influxdb
```

#### Create Database
```bash
influx -execute "CREATE DATABASE varken"
```

#### Configuration
```ini
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
ssl = false
verify_ssl = false
user = 
password = 
db = varken
```

### Option 2: InfluxDB v2

#### Install with Docker
```bash
docker run -d \
  --name influxdb2 \
  -p 8086:8086 \
  -v influxdb2-data:/var/lib/influxdb2 \
  influxdb:2.7
```

#### Setup via Web UI
1. Open http://localhost:8086
2. Create account (remember username/password)
3. Create organization (e.g., "my-org")
4. Create bucket: "varken"
5. Generate token: Settings → Tokens → Generate

#### Configuration
```ini
[INFLUXDB2]
enabled = true
hostname = localhost
port = 8086
ssl = false
verify_ssl = false
token = your_generated_token_here
org = my-org
bucket = varken
```

### Option 3: TimescaleDB

#### Install TimescaleDB
```bash
# Add repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

# Install
sudo apt update
sudo apt install -y timescaledb-2-postgresql-14

# Setup
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Create Database
```bash
sudo -u postgres psql

CREATE DATABASE varken;
\c varken
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
```

#### Create User
```bash
sudo -u postgres psql -d varken

CREATE USER varken WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE varken TO varken;
GRANT ALL ON ALL TABLES IN SCHEMA public TO varken;
\q
```

#### Configuration
```ini
[TIMESCALEDB]
enabled = true
hostname = localhost
port = 5432
ssl = false
user = varken
password = your_secure_password
database = varken
```

### Option 4: QuestDB

#### Install with Docker
```bash
docker run -d \
  --name questdb \
  -p 9000:9000 \
  -p 9009:9009 \
  -v questdb-data:/var/lib/questdb \
  questdb/questdb
```

#### Verify
```bash
curl http://localhost:9000
```

#### Configuration
```ini
[QUESTDB]
enabled = true
hostname = localhost
port = 9000
ssl = false
user = 
password = 
```

### Option 5: VictoriaMetrics

#### Install with Docker
```bash
docker run -d \
  --name victoriametrics \
  -p 8428:8428 \
  -v victoria-data:/victoria-metrics-data \
  victoriametrics/victoria-metrics:latest
```

#### Verify
```bash
curl http://localhost:8428/metrics
```

#### Configuration
```ini
[VICTORIAMETRICS]
enabled = true
hostname = localhost
port = 8428
ssl = false
user = 
password = 
```

---

## Configuration

### Step 1: Create Configuration File

```bash
# Copy example config
sudo cp /opt/Varken/data/varken.example.ini /opt/Varken/data/varken.ini

# Or use the clean example
sudo cp /path/to/varken_clean.ini /opt/Varken/data/varken.ini

# Edit configuration
sudo nano /opt/Varken/data/varken.ini
```

### Step 2: Configure Global Settings

```ini
[global]
sonarr_server_ids = 1,2      # Enable Sonarr servers 1 and 2
radarr_server_ids = 1,2      # Enable Radarr servers 1 and 2
lidarr_server_ids = false    # Disable Lidarr
tautulli_server_ids = 1      # Enable Tautulli server 1
ombi_server_ids = false      # Disable Ombi
sickchill_server_ids = false # Disable SickChill
unifi_server_ids = false     # Disable UniFi
maxmind_license_key = your_maxmind_key  # Optional: for GeoIP
```

### Step 3: Configure Databases

Enable at least one database:

```ini
# Example: Enable InfluxDB v1 and TimescaleDB
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
ssl = false
verify_ssl = false
user = 
password = 
db = varken

[INFLUXDB2]
enabled = false  # Disabled

[INFLUXDB3]
enabled = false  # Disabled

[TIMESCALEDB]
enabled = true
hostname = localhost
port = 5432
ssl = false
user = varken
password = your_password
database = varken

[QUESTDB]
enabled = false  # Disabled

[VICTORIAMETRICS]
enabled = false  # Disabled
```

### Step 4: Configure Services

Configure your monitoring targets:

#### Tautulli (Plex)
```ini
[tautulli-1]
url = http://192.168.1.100:8181
fallback_ip = 1.1.1.1
apikey = your_tautulli_api_key
ssl = false
verify_ssl = false
get_activity = true
get_activity_run_seconds = 30
get_stats = true
get_stats_run_seconds = 3600
```

**Getting API Key:**
1. Open Tautulli web interface
2. Settings → Web Interface → API
3. Copy API Key

#### Sonarr
```ini
[sonarr-1]
url = http://192.168.1.100:8989
apikey = your_sonarr_api_key
ssl = false
verify_ssl = false
missing_days = 7
missing_days_run_seconds = 300
future_days = 1
future_days_run_seconds = 300
queue = true
queue_run_seconds = 300
```

**Getting API Key:**
1. Open Sonarr
2. Settings → General → Security → API Key

#### Radarr
```ini
[radarr-1]
url = http://192.168.1.100:7878
apikey = your_radarr_api_key
ssl = false
verify_ssl = false
queue = true
queue_run_seconds = 300
get_missing = true
get_missing_run_seconds = 300
```

### Step 5: Set Permissions

```bash
sudo chown varken:varken /opt/Varken/data/varken.ini
sudo chmod 600 /opt/Varken/data/varken.ini  # Secure config file
```

---

## Setup Systemd Service

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/varken.service
```

Paste this content:

```ini
[Unit]
Description=Varken - Multi-Database Metrics Aggregator
After=network.target influxdb.service postgresql.service
Wants=influxdb.service postgresql.service

[Service]
Type=simple
User=varken
Group=varken
WorkingDirectory=/opt/Varken
Environment="DATA_FOLDER=/opt/Varken/data"
ExecStart=/usr/bin/python3 /opt/Varken/Varken.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Save and exit.

### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable varken

# Start service
sudo systemctl start varken

# Check status
sudo systemctl status varken
```

### Step 3: View Logs

```bash
# Live logs
sudo journalctl -u varken -f

# Last 100 lines
sudo journalctl -u varken -n 100

# Today's logs
sudo journalctl -u varken --since today
```

---

## Verification

### Check Service Status

```bash
sudo systemctl status varken
```

**Expected output:**
```
● varken.service - Varken - Multi-Database Metrics Aggregator
   Loaded: loaded (/etc/systemd/system/varken.service; enabled)
   Active: active (running) since Wed 2026-01-09 20:00:00 EST
```

### Check Database Connections

```bash
sudo journalctl -u varken -n 100 | grep -i "successfully connected"
```

**Expected output:**
```
Successfully connected to influxdb1 at localhost:8086
Successfully connected to timescale at localhost:5432
✓ Connected to 2 database(s)
```

### Check for Errors

```bash
sudo journalctl -u varken -n 100 | grep -iE "error|fail|critical"
```

**Should see no errors** (or only minor warnings).

### Test Database Writes

Wait 30-60 seconds for first data collection, then check:

#### InfluxDB v1
```bash
influx -database varken -execute "SELECT * FROM tautulli LIMIT 5"
```

#### InfluxDB v2
```bash
influx query 'from(bucket: "varken") |> range(start: -5m) |> limit(n: 5)'
```

#### TimescaleDB
```bash
sudo -u postgres psql -d varken -c "SELECT time, stream_count FROM varken_metrics ORDER BY time DESC LIMIT 5;"
```

#### QuestDB
```bash
curl "http://localhost:9000/exec?query=SELECT%20*%20FROM%20tautulli%20LIMIT%205"
```

#### VictoriaMetrics
```bash
curl "http://localhost:8428/api/v1/query?query=tautulli_stream_count"
```

### Check Data Flow

```bash
# Watch live activity
sudo journalctl -u varken -f

# Should see entries like:
# get_activity: Tautulli
# Writing to 2 database(s)
# Write successful to influxdb1
# Write successful to timescale
```

---

## Grafana Integration

### Install Grafana

#### Ubuntu/Debian
```bash
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

#### Access Grafana
Open http://localhost:3000

Default credentials:
- Username: `admin`
- Password: `admin`

### Add Data Sources

#### InfluxDB v1
1. Configuration → Data Sources → Add data source
2. Select **InfluxDB**
3. Configure:
   - URL: `http://localhost:8086`
   - Database: `varken`
   - User: (if auth enabled)
   - Password: (if auth enabled)
4. Save & Test

#### InfluxDB v2
1. Configuration → Data Sources → Add data source
2. Select **InfluxDB**
3. Configure:
   - Query Language: **Flux**
   - URL: `http://localhost:8086`
   - Organization: `my-org`
   - Token: `your_token`
   - Default Bucket: `varken`
4. Save & Test

#### TimescaleDB
1. Configuration → Data Sources → Add data source
2. Select **PostgreSQL**
3. Configure:
   - Host: `localhost:5432`
   - Database: `varken`
   - User: `varken`
   - Password: `your_password`
   - SSL Mode: `disable`
   - Version: `14+`
   - TimescaleDB: **Enable**
4. Save & Test

#### QuestDB
1. Configuration → Data Sources → Add data source
2. Select **PostgreSQL**
3. Configure:
   - Host: `localhost:8812`
   - Database: `qdb`
   - User: `admin`
   - Password: `quest`
   - SSL Mode: `disable`
4. Save & Test

#### VictoriaMetrics
1. Configuration → Data Sources → Add data source
2. Select **Prometheus**
3. Configure:
   - URL: `http://localhost:8428`
4. Save & Test

### Import Dashboards

#### Official Varken Dashboards
1. Download from: https://github.com/Boerderij/Varken/tree/develop/grafana
2. In Grafana: Dashboards → Import
3. Upload JSON file
4. Select your data source
5. Import

#### Community Dashboards
1. Visit https://grafana.com/grafana/dashboards/
2. Search for "Varken" or "Tautulli"
3. Copy Dashboard ID
4. In Grafana: Dashboards → Import → Load by ID

---

## Troubleshooting

### Issue: Service Won't Start

**Check logs:**
```bash
sudo journalctl -u varken -n 50
```

**Common causes:**
1. **Python not found**: Install python3
2. **Missing dependencies**: Run `pip3 install -r requirements.txt`
3. **Config errors**: Check syntax in varken.ini
4. **Permission denied**: Fix with `sudo chown -R varken:varken /opt/Varken`

### Issue: No Database Connections

**Check config:**
```bash
grep -A 10 "\[INFLUXDB\]" /opt/Varken/data/varken.ini
```

**Verify `enabled = true` is set for at least one database.**

**Test database connectivity:**
```bash
# InfluxDB
curl http://localhost:8086/ping

# TimescaleDB
sudo -u postgres psql -d varken -c "SELECT 1;"

# QuestDB
curl http://localhost:9000
```

### Issue: Database Write Errors

**Check database is running:**
```bash
# InfluxDB
sudo systemctl status influxdb

# PostgreSQL (TimescaleDB)
sudo systemctl status postgresql

# Docker databases
docker ps
```

**Check credentials:**
```bash
# Test manually
influx -username root -password root -database varken -execute "SHOW MEASUREMENTS"
```

### Issue: Import Errors

**If you see:**
```
ModuleNotFoundError: No module named 'influxdb_client'
```

**Fix:**
```bash
sudo pip3 install influxdb-client psycopg2-binary --break-system-packages
```

### Issue: Permission Denied

**Fix permissions:**
```bash
sudo chown -R varken:varken /opt/Varken
sudo chmod 755 /opt/Varken
sudo chmod 600 /opt/Varken/data/varken.ini
```

### Issue: High CPU/Memory Usage

**Check number of enabled databases:**
```bash
grep "enabled = true" /opt/Varken/data/varken.ini
```

Each database adds ~3-5% CPU and ~10MB RAM.

**Reduce collection frequency:**
```ini
[tautulli-1]
get_activity_run_seconds = 60  # Increase from 30
get_stats_run_seconds = 7200    # Increase from 3600
```

### Get Help

**View full logs:**
```bash
sudo journalctl -u varken --no-pager | tail -200
```

**Test configuration:**
```bash
cd /opt/Varken
python3 Varken.py  # Run in foreground
```

**Check Python imports:**
```bash
python3 -c "from varken.dbmanager_v2 import DBManager; print('OK')"
python3 -c "from varken.iniparser_v2 import EnhancedINIParser; print('OK')"
```

---

## Upgrading from Original Varken

If you already have Varken installed:

### Step 1: Backup

```bash
# Backup current installation
sudo cp -r /opt/Varken /opt/Varken.backup

# Backup config
sudo cp /opt/Varken/data/varken.ini /opt/Varken/data/varken.ini.backup
```

### Step 2: Stop Current Varken

```bash
sudo systemctl stop varken
```

### Step 3: Install Enhanced Files

```bash
# Copy new files
sudo cp dbmanager_v2_questdb_fixed.py /opt/Varken/varken/dbmanager_v2.py
sudo cp iniparser_v2_complete.py /opt/Varken/varken/iniparser_v2.py

# Install new dependencies
sudo pip3 install influxdb-client psycopg2-binary --break-system-packages
```

### Step 4: Update Configuration

Your existing config will work, but add database sections:

```bash
sudo nano /opt/Varken/data/varken.ini
```

Change:
```ini
[influxdb]  # Old format (lowercase)
```

To:
```ini
[INFLUXDB]  # New format (uppercase)
enabled = true  # Add this line
```

Add sections for any additional databases you want.

### Step 5: Update Varken.py

Make the three changes to Varken.py as described in [Step 6](#step-6-update-varkenpy) above.

### Step 6: Restart and Verify

```bash
# Start service
sudo systemctl start varken

# Check status
sudo systemctl status varken

# View logs
sudo journalctl -u varken -n 50
```

### Step 7: Rollback if Needed

If something goes wrong:

```bash
# Stop new version
sudo systemctl stop varken

# Restore backup
sudo rm -rf /opt/Varken
sudo mv /opt/Varken.backup /opt/Varken

# Restart
sudo systemctl start varken
```

---

## Post-Installation

### Regular Maintenance

**Update Varken:**
```bash
cd /opt/Varken
sudo git pull
sudo systemctl restart varken
```

**Check logs weekly:**
```bash
sudo journalctl -u varken --since "7 days ago" | grep -iE "error|fail"
```

**Backup configuration:**
```bash
sudo cp /opt/Varken/data/varken.ini ~/varken-config-backup-$(date +%Y%m%d).ini
```

### Performance Tuning

**Monitor resource usage:**
```bash
# CPU and Memory
ps aux | grep Varken

# Service status
sudo systemctl status varken
```

**Optimize collection intervals** if needed:
```ini
# Reduce frequency for less critical stats
get_stats_run_seconds = 7200  # Every 2 hours instead of 1
```

### Security Hardening

**Secure config file:**
```bash
sudo chmod 600 /opt/Varken/data/varken.ini
```

**Use secrets manager** (future enhancement):
```ini
# Instead of plain text passwords
password = ${INFLUXDB_PASSWORD}  # From environment
```

**Firewall rules:**
```bash
# Only allow local connections to databases
sudo ufw deny 8086  # InfluxDB
sudo ufw deny 5432  # PostgreSQL
sudo ufw allow from 192.168.1.0/24 to any port 8086  # Allow local network
```

---

## Next Steps

1. **Set up Grafana dashboards** - Import official Varken dashboards
2. **Configure alerting** - Get notified of issues
3. **Add more databases** - Try QuestDB or VictoriaMetrics
4. **Optimize retention** - Configure data retention policies
5. **Monitor performance** - Set up Prometheus metrics (future)

---

## Summary

You now have a powerful multi-database Varken installation that can:

- ✅ Write to multiple databases simultaneously
- ✅ Provide redundancy and backup
- ✅ Enable easy database migration
- ✅ Support testing new databases
- ✅ Run as a systemd service
- ✅ Auto-start on boot
- ✅ Integrate with Grafana

**Congratulations! Your installation is complete!** 🎉

For more information:
- **Documentation**: See other GUIDE.md files
- **Troubleshooting**: See TROUBLESHOOTING.md
- **Enhancements**: See ENHANCEMENT_SUGGESTIONS.md

---

## Quick Reference

### Common Commands

```bash
# Service management
sudo systemctl start varken
sudo systemctl stop varken
sudo systemctl restart varken
sudo systemctl status varken

# Logs
sudo journalctl -u varken -f          # Live logs
sudo journalctl -u varken -n 100      # Last 100 lines
sudo journalctl -u varken --since today  # Today's logs

# Configuration
sudo nano /opt/Varken/data/varken.ini

# Test run
cd /opt/Varken && python3 Varken.py
```

### File Locations

- **Installation**: `/opt/Varken`
- **Configuration**: `/opt/Varken/data/varken.ini`
- **Service**: `/etc/systemd/system/varken.service`
- **Logs**: `journalctl -u varken`
- **Enhanced files**: `/opt/Varken/varken/dbmanager_v2.py`, `iniparser_v2.py`

### Support

- **Original Varken**: https://github.com/Boerderij/Varken
- **Issues**: Check logs first with `sudo journalctl -u varken -n 100`
- **Documentation**: Review included GUIDE.md files
