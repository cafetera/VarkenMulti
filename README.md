# Varken Multi-Database - Quick Start Guide

Get Varken running with multi-database support in **5 minutes**!

## 🚀 Installation

### Step 1: Clone & Install (2 minutes)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/varken-multi-db.git /opt/Varken
cd /opt/Varken

# Run automated installer
sudo ./install.sh
```

The installer handles everything automatically!

### Step 2: Configure (2 minutes)

Edit the configuration file:

```bash
sudo nano /opt/Varken/data/varken.ini
```

**Minimal configuration:**

```ini
[global]
tautulli_server_ids = 1

# Enable InfluxDB
[INFLUXDB]
enabled = true
hostname = localhost
port = 8086
user = root
password = root
db = varken

# Configure Tautulli
[tautulli-1]
url = http://YOUR_TAUTULLI_IP:8181
apikey = YOUR_TAUTULLI_API_KEY
ssl = false
get_activity = true
get_activity_run_seconds = 30
get_stats = true
get_stats_run_seconds = 3600
```

**Save and exit** (Ctrl+X, Y, Enter)

### Step 3: Start Varken (1 minute)

```bash
# Start Varken
sudo systemctl start varken

# Check status
sudo systemctl status varken

# View logs
sudo journalctl -u varken -f
```

**Expected output:**
```
Successfully connected to influxdb1 at localhost:8086
✓ Connected to 1 database(s)
Running job: get_activity
```

Press `Ctrl+C` to exit logs.

## ✅ Verification

### Check if data is being written:

```bash
# InfluxDB v1
influx -execute "SHOW DATABASES"
influx -execute "SELECT COUNT(*) FROM tautulli" -database="varken"
```

Should show data!

## 🎨 Grafana Setup (Optional)

1. **Add InfluxDB data source:**
   - Go to Configuration → Data Sources
   - Add InfluxDB
   - URL: `http://localhost:8086`
   - Database: `varken`
   - Save & Test

2. **Import dashboard:**
   - Dashboards → Import
   - Upload from `/opt/Varken/grafana-dashboards/`

## 🔧 Troubleshooting

### Varken won't start?

```bash
# Check logs
sudo journalctl -u varken -n 50

# Test configuration
python3 -c "import configparser; configparser.ConfigParser().read('/opt/Varken/data/varken.ini')"
```

### No data in database?

```bash
# Check if InfluxDB is running
curl http://localhost:8086/ping

# Check Varken logs
sudo journalctl -u varken -f
```

### Connection errors?

```bash
# Test Tautulli connection
curl "http://YOUR_TAUTULLI_IP:8181/api/v2?apikey=YOUR_KEY&cmd=get_activity"
```

## 🚀 Add More Databases

Want to use multiple databases? Easy!

```bash
sudo nano /opt/Varken/data/varken.ini
```

Add more database sections:

```ini
# TimescaleDB
[TIMESCALEDB]
enabled = true
hostname = localhost
port = 5432
user = postgres
password = password
database = varken

# VictoriaMetrics
[VICTORIAMETRICS]
enabled = true
hostname = localhost
port = 8428
```

Restart:
```bash
sudo systemctl restart varken
```

Data now writes to all enabled databases!

## 📚 Learn More

- **[INSTALLATION.md](INSTALLATION.md)** - Detailed installation guide
- **[MULTI_DATABASE_GUIDE.md](MULTI_DATABASE_GUIDE.md)** - Using multiple databases
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues

## 💡 Pro Tips

1. **Enable auto-start:**
   ```bash
   sudo systemctl enable varken
   ```

2. **Monitor logs in real-time:**
   ```bash
   sudo journalctl -u varken -f
   ```

3. **Test before enabling services:**
   - Start with just Tautulli
   - Verify data is flowing
   - Then add Sonarr, Radarr, etc.

## 🎉 You're Done!

Varken is now collecting metrics from Tautulli and writing to your database(s)!

**Next steps:**
- Set up Grafana dashboards
- Add more services (Sonarr, Radarr)
- Enable additional databases
- Customize collection intervals

## 🆘 Need Help?

- Check [INSTALLATION.md](INSTALLATION.md) for detailed instructions
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Create an issue on GitHub

---

**That's it! You're running Varken with multi-database support!** 🎊