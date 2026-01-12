# Varken Multi-Database - Installation Guide

Complete installation guide for Varken with multi-database support.

**Repository**: https://github.com/YOUR_USERNAME/varken-multi-db

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Database Setup](#database-setup)
- [Configuration](#configuration)
- [Starting Varken](#starting-varken)
- [Verification](#verification)
- [Grafana Integration](#grafana-integration)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### One-Command Installation

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/varken-multi-db.git /opt/Varken
cd /opt/Varken
sudo ./install.sh
```

**That's it!** The install script handles everything automatically.

Then configure your databases in `/opt/Varken/data/varken.ini` and restart:

```bash
sudo nano /opt/Varken/data/varken.ini
sudo systemctl restart varken
```

---

## 📦 Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+, or similar)
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum (1GB+ recommended)
- **Disk**: 1GB free space

### Check Python Version

```bash
python3 --version
# Should show: Python 3.8.x or higher
```

### Supported Databases (Choose at least ONE)

- ✅ InfluxDB v1.8+
- ✅ InfluxDB v2.x
- ✅ InfluxDB v3 (Cloud/Core)
- ✅ TimescaleDB (PostgreSQL 12+ with TimescaleDB extension)
- ✅ QuestDB 6.0+
- ✅ VictoriaMetrics 1.90+

### Supported Services (Configure as needed)

- Tautulli (Plex)
- Sonarr
- Radarr
- Lidarr
- Ombi
- SickChill
- UniFi

---

## 💻 Installation Methods

### Method 1: Automated Install (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/varken-multi-db.git /opt/Varken
cd /opt/Varken

# 2. Run installer
sudo ./install.sh

# 3. Edit configuration
sudo nano /opt/Varken/data/varken.ini

# 4. Start Varken
sudo systemctl start varken
```

**The installer automatically:**
- ✅ Installs Python dependencies
- ✅ Creates configuration from template
- ✅ Sets up systemd service
- ✅ Configures permissions
- ✅ Enables auto-start on boot

---

### Method 2: Manual Installation

#### Step 1: Install System Packages

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip git
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip git
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip git
```

#### Step 2: Clone Repository

```bash
# Clone to /opt/Varken
sudo git clone https://github.com/YOUR_USERNAME/varken-multi-db.git /opt/Varken
cd /opt/Varken
```

#### Step 3: Install Python Dependencies

```bash
sudo pip3 install -r requirements.txt --break-system-packages
```

**Dependencies installed:**
- influxdb (InfluxDB v1)
- influxdb-client (InfluxDB v2/v3)
- psycopg2-binary (TimescaleDB)
- requests (QuestDB, VictoriaMetrics)
- schedule (Job scheduling)
- GeoIP2-database (MaxMind GeoIP)

#### Step 4: Create Configuration

```bash
# Copy example config
sudo cp varken.example.ini data/varken.ini

# Edit configuration
sudo nano data/varken.ini
```

#### Step 5: Install Systemd Service

```bash
# Copy service file
sudo cp varken.service /etc/systemd/system/varken.service

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable varken
```

#### Step 6: Start Varken

```bash
sudo systemctl start varken
```

---

### Method 3: Docker Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/varken-multi-db.git
cd varken-multi-db

# Edit docker-compose.yml and add your config
nano docker-compose.yml

# Start with Docker Compose
docker-compose up -d
```

**Docker Compose Example:**
```yaml
version: '3.8'

services:
  varken:
    build: .
    container_name: varken
    volumes:
      - ./data:/app/data
    environment:
      - TZ=America/New_York
    restart: unless-stopped
```

---

## 🗄️ Database Setup

You need **at least ONE database**. Here's how to set up each:

### InfluxDB v1 (Easiest)

**Install InfluxDB:**
```bash
# Ubuntu/Debian
wget -q https://repos.influxdata.com/influxdata-archive_compat.key
echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
sudo apt update && sudo apt install influxdb
sudo systemctl start influxdb
sudo systemctl enable influxdb

# Create database
influx -execute "CREATE DATABASE varken"
```

**Or with Docker:**
```bash
docker run -d \
  --name influxdb \
  -p 8086:8086 \
  -v influxdb-data:/var/lib/influxdb \
  influxdb:1.8
```

**Configure in varken.ini:**
```ini
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
user = root
password = root
db = varken
```

---

### InfluxDB v2

**Install InfluxDB v2:**
```bash
# Ubuntu/Debian
wget https://dl.influxdata.com/influxdb/releases/influxdb2-2.7.4-amd64.deb
sudo dpkg -i influxdb2-2.7.4-amd64.deb
sudo systemctl start influxdb
sudo systemctl enable influxdb
```

**Or with Docker:**
```bash
docker run -d \
  --name influxdb2 \
  -p 8086:8086 \
  -v influxdb2-data:/var/lib/influxdb2 \
  influxdb:2.7
```

**Setup via UI:**
1. Open http://localhost:8086
2. Create initial user and organization
3. Create bucket named `varken`
4. Generate API token

**Configure in varken.ini:**
```ini
[INFLUXDB2]
enabled = true
hostname = localhost
port = 8086
ssl = false
token = YOUR_API_TOKEN
org = YOUR_ORG_NAME
bucket = varken
```

---

### TimescaleDB

**Install TimescaleDB:**
```bash
# Add PostgreSQL repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt update

# Install TimescaleDB
sudo apt install timescaledb-2-postgresql-14

# Configure PostgreSQL
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql

# Create database and enable extension
sudo -u postgres psql -c "CREATE DATABASE varken;"
sudo -u postgres psql -d varken -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

**Or with Docker:**
```bash
docker run -d \
  --name timescaledb \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -v timescale-data:/var/lib/postgresql/data \
  timescale/timescaledb:latest-pg14
```

**Configure in varken.ini:**
```ini
[TIMESCALEDB]
enabled = true
hostname = localhost
port = 5432
user = postgres
password = password
database = varken
```

---

### QuestDB

**Install QuestDB:**
```bash
# Download and run
wget https://github.com/questdb/questdb/releases/download/7.3.10/questdb-7.3.10-rt-linux-amd64.tar.gz
tar -xvf questdb-7.3.10-rt-linux-amd64.tar.gz
cd questdb-7.3.10-rt-linux-amd64
./questdb.sh start
```

**Or with Docker:**
```bash
docker run -d \
  --name questdb \
  -p 9000:9000 \
  -p 8812:8812 \
  -v questdb-data:/var/lib/questdb \
  questdb/questdb:latest
```

**Configure in varken.ini:**
```ini
[QUESTDB]
enabled = true
hostname = localhost
port = 9000
ssl = false
```

---

### VictoriaMetrics

**Install VictoriaMetrics:**
```bash
# Download binary
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v1.96.0/victoria-metrics-linux-amd64-v1.96.0.tar.gz
tar -xzf victoria-metrics-linux-amd64-v1.96.0.tar.gz
sudo mv victoria-metrics-prod /usr/local/bin/

# Create systemd service
sudo tee /etc/systemd/system/victoriametrics.service > /dev/null <<EOF
[Unit]
Description=VictoriaMetrics
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/victoria-metrics-prod
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start victoriametrics
sudo systemctl enable victoriametrics
```

**Or with Docker:**
```bash
docker run -d \
  --name victoriametrics \
  -p 8428:8428 \
  -v victoria-data:/victoria-metrics-data \
  victoriametrics/victoria-metrics:latest
```

**Configure in varken.ini:**
```ini
[VICTORIAMETRICS]
enabled = true
hostname = localhost
port = 8428
ssl = false
```

---

## ⚙️ Configuration

### Basic Configuration

Edit `/opt/Varken/data/varken.ini`:

```bash
sudo nano /opt/Varken/data/varken.ini
```

### Minimal Working Example

```ini
[global]
tautulli_server_ids = 1
maxmind_license_key = YOUR_MAXMIND_KEY

# Enable InfluxDB v1
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
user = root
password = root
db = varken

# Configure Tautulli
[tautulli-1]
url = http://tautulli.local:8181
apikey = YOUR_TAUTULLI_API_KEY
ssl = false
get_activity = true
get_activity_run_seconds = 30
get_stats = true
get_stats_run_seconds = 3600
```

### Multi-Database Configuration

Enable multiple databases for redundancy:

```ini
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
user = root
password = root
db = varken

[TIMESCALEDB]
enabled = true
hostname = localhost
port = 5432
user = postgres
password = password
database = varken

[VICTORIAMETRICS]
enabled = true
hostname = localhost
port = 8428
```

Data will be written to **all enabled databases simultaneously**!

### Service Configuration

Configure your media services:

```ini
# Sonarr
[sonarr-1]
url = http://sonarr.local:8989
apikey = YOUR_SONARR_API_KEY
ssl = false
queue = true
queue_run_seconds = 300

# Radarr
[radarr-1]
url = http://radarr.local:7878
apikey = YOUR_RADARR_API_KEY
ssl = false
queue = true
queue_run_seconds = 300
```

### Configuration Reference

See the complete configuration guide:
```bash
cat /opt/Varken/docs/CONFIGURATION.md
```

---

## 🎬 Starting Varken

### Using Systemd (Recommended)

```bash
# Start Varken
sudo systemctl start varken

# Enable auto-start on boot
sudo systemctl enable varken

# Check status
sudo systemctl status varken

# View logs
sudo journalctl -u varken -f
```

### Running Manually (for testing)

```bash
cd /opt/Varken
python3 Varken.py
```

Press `Ctrl+C` to stop.

### Using Docker

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## ✅ Verification

### Check Service Status

```bash
sudo systemctl status varken
```

**Expected output:**
```
● varken.service - Varken - Plex Ecosystem Metrics Aggregator
   Loaded: loaded
   Active: active (running)
```

### Check Logs

```bash
sudo journalctl -u varken -n 50
```

**Look for:**
```
Successfully connected to influxdb1 at localhost:8086
Successfully connected to timescaledb at localhost:5432
✓ Connected to 2 database(s)
```

### Test Database Connections

```bash
cd /opt/Varken
python3 -c "
import sys
sys.path.insert(0, '/opt/Varken')
from varken.iniparser_v2 import EnhancedINIParser
CONFIG = EnhancedINIParser('/opt/Varken/data/varken.ini')
print(f'Enabled databases: {len(CONFIG.get_enabled_databases())}')
for db in CONFIG.get_enabled_databases():
    print(f'  - {db.db_type} at {db.url}:{db.port}')
"
```

### Verify Data is Being Written

**InfluxDB v1:**
```bash
influx -execute "SELECT COUNT(*) FROM tautulli"
```

**InfluxDB v2:**
```bash
influx query 'from(bucket: "varken") |> range(start: -1h) |> count()'
```

**TimescaleDB:**
```bash
psql -U postgres -d varken -c "SELECT COUNT(*) FROM varken_metrics;"
```

**QuestDB:**
```bash
curl "http://localhost:9000/exec?query=SELECT%20count()%20FROM%20tautulli"
```

**VictoriaMetrics:**
```bash
curl "http://localhost:8428/api/v1/query?query=tautulli_stream_count"
```

---

## 📊 Grafana Integration

### Add Data Sources

#### InfluxDB
1. Go to **Configuration → Data Sources → Add data source**
2. Select **InfluxDB**
3. Configure:
   - **Query Language**: InfluxQL (for v1) or Flux (for v2)
   - **URL**: http://localhost:8086
   - **Database**: varken (v1) or leave blank (v2)
   - **Token**: Your API token (v2 only)
4. Click **Save & Test**

#### TimescaleDB
1. Select **PostgreSQL**
2. Configure:
   - **Host**: localhost:5432
   - **Database**: varken
   - **User**: postgres
   - **Password**: your_password
   - **TLS/SSL Mode**: disable
3. Click **Save & Test**

#### VictoriaMetrics
1. Select **Prometheus**
2. Configure:
   - **URL**: http://localhost:8428
3. Click **Save & Test**

### Import Dashboards

```bash
# Dashboards are in the repo
ls /opt/Varken/grafana-dashboards/
```

Import via Grafana UI:
1. Go to **Dashboards → Import**
2. Click **Upload JSON file**
3. Select dashboard from `/opt/Varken/grafana-dashboards/`
4. Choose your data source
5. Click **Import**

---

## 🔧 Troubleshooting

### Varken Won't Start

**Check logs:**
```bash
sudo journalctl -u varken -n 100 --no-pager
```

**Common issues:**
- Missing Python dependencies
- Invalid configuration
- Database not running
- Wrong permissions

**Solution:**
```bash
# Reinstall dependencies
sudo pip3 install -r /opt/Varken/requirements.txt --break-system-packages

# Check config syntax
python3 -c "import configparser; configparser.ConfigParser().read('/opt/Varken/data/varken.ini')"

# Fix permissions
sudo chown -R root:root /opt/Varken
sudo chmod 755 /opt/Varken
sudo chmod 644 /opt/Varken/data/varken.ini
```

### Database Connection Failed

**Test connection manually:**

**InfluxDB:**
```bash
curl http://localhost:8086/ping
```

**TimescaleDB:**
```bash
psql -U postgres -d varken -c "SELECT version();"
```

**QuestDB:**
```bash
curl http://localhost:9000/exec?query=SELECT%201
```

**VictoriaMetrics:**
```bash
curl http://localhost:8428/metrics
```

### No Data in Database

**Check if services are configured:**
```bash
grep "server_ids" /opt/Varken/data/varken.ini
```

**Enable at least one service:**
```ini
[global]
tautulli_server_ids = 1  # Enable Tautulli
```

**Verify service is reachable:**
```bash
curl http://tautulli.local:8181/api/v2?apikey=YOUR_KEY&cmd=get_activity
```

### High CPU/Memory Usage

**Check if too many databases enabled:**
```bash
grep "^enabled = true" /opt/Varken/data/varken.ini | wc -l
```

**Reduce write frequency:**
```ini
[tautulli-1]
get_activity_run_seconds = 60  # Increase from 30
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R root:root /opt/Varken

# Fix permissions
sudo chmod 755 /opt/Varken
sudo chmod 755 /opt/Varken/varken
sudo chmod 644 /opt/Varken/data/varken.ini
```

### Systemd Service Issues

```bash
# Reload systemd
sudo systemctl daemon-reload

# Check service file
sudo systemctl cat varken

# Check service status
sudo systemctl status varken

# Restart service
sudo systemctl restart varken
```

---

## 🔄 Upgrading

### From GitHub

```bash
# Stop Varken
sudo systemctl stop varken

# Backup configuration
sudo cp /opt/Varken/data/varken.ini /opt/Varken/data/varken.ini.backup

# Pull latest changes
cd /opt/Varken
sudo git pull

# Update dependencies
sudo pip3 install -r requirements.txt --break-system-packages --upgrade

# Restart Varken
sudo systemctl start varken
```

### From Original Varken

See the migration guide:
```bash
cat /opt/Varken/docs/MIGRATION_GUIDE.md
```

---

## 📚 Additional Documentation

- **Configuration Guide**: `/opt/Varken/docs/CONFIGURATION.md`
- **Multi-Database Guide**: `/opt/Varken/docs/MULTI_DATABASE_GUIDE.md`
- **Migration Guide**: `/opt/Varken/docs/MIGRATION_GUIDE.md`
- **Troubleshooting**: `/opt/Varken/docs/TROUBLESHOOTING.md`
- **Enhancement Suggestions**: `/opt/Varken/docs/ENHANCEMENT_SUGGESTIONS.md`

---

## 🆘 Getting Help

### Check Logs
```bash
sudo journalctl -u varken -n 100
```

### Run Debug Script
```bash
cd /opt/Varken
python3 debug_varken_config.py
```

### Test Database Connection
```bash
python3 test_influxdb_connection.py
```

### Report Issues

1. Check existing issues: https://github.com/YOUR_USERNAME/varken-multi-db/issues
2. Create new issue with:
   - Varken version
   - Python version
   - OS version
   - Database versions
   - Full error logs
   - Configuration (remove passwords!)

---

## 🎉 Success!

If you see this in your logs, you're all set:

```
Successfully connected to influxdb1 at localhost:8086
Successfully connected to timescaledb at localhost:5432
✓ Connected to 2 database(s)
MaxMind DB will update in 27 days
Running job: get_activity
```

Your Varken multi-database setup is now running! 🚀

### Next Steps:

1. **Set up Grafana** - Visualize your metrics
2. **Add more databases** - Enable redundancy
3. **Configure services** - Add Sonarr, Radarr, etc.
4. **Review enhancements** - See ENHANCEMENT_SUGGESTIONS.md

---

## 📄 License

MIT License - See LICENSE file

## 🙏 Credits

- Original Varken: https://github.com/Boerderij/Varken
- Multi-Database Enhancement: This project

---

**Star the repo if this helped you!** ⭐