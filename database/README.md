# CyberShield Database Backup

This directory contains the complete PostgreSQL database backup for **CyberShield**, including:
- All schema migrations and table structures (`users`, `scan_history`, `email_scan_history`, `qr_scan_history`, `blacklist_entries`, `detection_rules`, `audit_logs`, etc.)
- Seed users (including Admin and standard users)
- Threat intelligence, sample scans, and pre-configured blacklist entries

## Restore Instructions

### Option 1: Using Docker Compose
If running PostgreSQL via Docker:
```bash
docker exec -i cybershield-postgres-1 psql -U cybershield -d cybershield < database/cybershield_backup.sql
```

### Option 2: Using local PostgreSQL (psql)
```bash
psql -U cybershield -d cybershield -f database/cybershield_backup.sql
```
