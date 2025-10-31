#!/bin/bash

# Database restore script for Arbitrage Bot
# Usage: ./scripts/restore-database.sh <backup_file>

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-arbitrage_bot}"
DB_USER="${DB_USER:-arbitrage_user}"

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/postgres/arbitrage_bot_20240115_020000.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "✗ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Confirm with user
echo "WARNING: This will overwrite the database '$DB_NAME'"
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo "Starting database restore at $(date)"

# Stop services (if running via Docker)
echo "Stopping services..."
docker-compose stop api_server backend 2>/dev/null || true

# Drop and recreate database
echo "Dropping existing database..."
if PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>/dev/null; then
    echo "✓ Database dropped"
else
    echo "⚠ Database drop failed (may not exist)"
fi

echo "Creating new database..."
if PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -c "CREATE DATABASE $DB_NAME;" 2>/dev/null; then
    echo "✓ Database created"
else
    echo "✗ Database creation failed"
    exit 1
fi

# Restore from backup
echo "Restoring from backup..."
if PGPASSWORD="$DB_PASSWORD" pg_restore \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --no-owner \
    --no-acl \
    "$BACKUP_FILE"; then
    echo "✓ Restore completed successfully"
else
    echo "✗ Restore failed"
    exit 1
fi

# Verify restore
echo "Verifying restore..."
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "0")

echo "✓ Restored $TABLE_COUNT tables"

# Restart services
echo "Restarting services..."
docker-compose start api_server backend 2>/dev/null || true

echo "✓ Restore completed at $(date)"
exit 0
