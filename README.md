# Varken Multi-Database Enhancement

## What is this?

**Enhanced Varken** that writes your Plex metrics to **6 different databases simultaneously** instead of just InfluxDB.

## Supported Databases

- ✅ InfluxDB (v1, v2, v3)
- ✅ TimescaleDB (PostgreSQL)
- ✅ QuestDB
- ✅ VictoriaMetrics

## Why?

### Multiple databases at once
Write to all enabled databases simultaneously - perfect for:
- **Migration**: Test new database while keeping old one running
- **Backup**: Store data in multiple places (local + cloud)
- **Cost savings**: Use free VictoriaMetrics for long-term storage
- **Testing**: Try new databases risk-free

### Better performance
- Auto-creates TimescaleDB columns with proper types
- Correct line protocol formatting for all databases
- Per-database error handling (one fails, others continue)

### 100% backward compatible
Works with your existing Varken config - just add new database sections.

## Quick Example

**Before:**
```
Tautulli → Varken → InfluxDB → Grafana
```

**After:**
```
                    ┌→ InfluxDB (production)
Tautulli → Varken ─┼→ TimescaleDB (SQL queries)
                    └→ VictoriaMetrics (free, unlimited retention)
```

## Installation

```bash
# 1. Copy enhanced files
sudo cp dbmanager_v2.py /opt/Varken/varken/
sudo cp iniparser_v2.py /opt/Varken/varken/

# 2. Enable databases in config
[INFLUXDB]
enabled = true

[TIMESCALEDB]
enabled = true

# 3. Restart
sudo systemctl restart varken
```

Done! Data now flows to all enabled databases.

## What's Included

**Code:**
- `dbmanager_v2.py` - 6 database backends
- `iniparser_v2.py` - Enhanced config parser
- `varken.service` - Systemd service

**Documentation:**
- Installation guide
- Database-specific guides
- Migration guides
- Troubleshooting
- 30+ enhancement ideas

## Real Benefits

- **Save money**: Free VictoriaMetrics vs paid InfluxDB Cloud
- **Zero downtime**: Migrate databases while keeping old one running
- **Flexibility**: Use different databases for different purposes
- **Reliability**: Redundant storage across multiple databases

## Quick Stats

| Feature | Original | Enhanced |
|---------|----------|----------|
| Databases | 1 | 6 |
| Multi-write | ❌ | ✅ |
| Auto-schema | ❌ | ✅ (TimescaleDB) |
| Line protocol | Basic | Production-grade |

## Get Started

See **INSTALLATION_GUIDE.md** - 15 minutes to setup.

---

**TL;DR**: Varken + write to 6 databases at once + better formatting + comprehensive docs = production-ready multi-database metrics platform! 🚀
