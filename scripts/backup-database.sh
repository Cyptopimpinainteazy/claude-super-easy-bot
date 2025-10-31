#!/bin/bash

# PostgreSQL backup script for Arbitrage Bot
# Usage: ./scripts/backup-database.sh
# Cron: 0 2 * * * /path/to/scripts/backup-database.sh >> /path/to/logs/backup.log 2>&1

set -e

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-arbitrage_bot}"
DB_USER="${DB_USER:-arbitrage_user}"
BACKUP_DIR="${BACKUP_DIR:-./backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/arbitrage_bot_$TIMESTAMP.sql.gz"

echo "Starting database backup at $(date)"
echo "Backup file: $BACKUP_FILE"

# Perform backup
if PGPASSWORD="$DB_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --file="$BACKUP_FILE"; then
    
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup completed successfully - Size: $BACKUP_SIZE"
    
    # Upload to S3 if configured
    if [ -n "$S3_BUCKET" ]; then
        echo "Uploading to S3..."
        if aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/postgres/" --sse AES256; then
            echo "✓ Uploaded to S3"
        else
            echo "✗ Failed to upload to S3"
        fi
    fi
    
    # Clean up old backups
    echo "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "arbitrage_bot_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
    echo "✓ Cleanup completed"
    
    exit 0
else
    echo "✗ Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi
