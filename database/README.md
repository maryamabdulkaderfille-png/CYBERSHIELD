# CyberShield Database

This directory contains the complete database scripts and backups for **CyberShield**.

## 1. Microsoft SQL Server (SSMS)
- **Database Script:** `cybershield_mssql.sql`
- **Database Name:** `CyberShieldDB`
- **Management Tool:** SQL Server Management Studio (SSMS)
- **Connection String (SQLAlchemy):**
  ```env
  DATABASE_URL=mssql+pyodbc://localhost/CyberShieldDB?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes
  ```

### How to Open / Restore in SSMS:
1. Open **SQL Server Management Studio (SSMS)**.
2. Connect to your local SQL Server instance (`localhost` or `.\SQLEXPRESS`).
3. Open `cybershield_mssql.sql` (`File -> Open -> File`).
4. Click **Execute (F5)** to create and populate `CyberShieldDB`.

---

## 2. PostgreSQL Backup (Alternative)
- **Backup File:** `cybershield_backup.sql`
- Can be restored using:
  ```bash
  psql -U cybershield -d cybershield -f database/cybershield_backup.sql
  ```
