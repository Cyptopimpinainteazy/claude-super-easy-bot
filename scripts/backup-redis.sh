#!/bin/bash

# Redis backup script for Arbitrage Bot
# Usage: ./scripts/backup-redis.sh
# Cron: 0 */6 * * * /path/to/scripts/backup-redis.sh >> /path/to/logs/backup.log 2>&1

set -e

# Configuration
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
BACKUP_DIR="${BACKUP_DIR:-./backups/redis}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DOCKER_CONTAINER="${DOCKER_CONTAINER:-arbitrage-redis}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting Redis backup at $(date)"

# Trigger Redis save
echo "Triggering Redis BGSAVE..."
if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE; then
    echo "✓ BGSAVE triggered"
else
    echo "✗ Failed to trigger BGSAVE"
    exit 1
fi

# Wait for save to complete (max 30 seconds)
echo "Waiting for save to complete..."
TIMEOUT=30
COUNT=0
while [ $COUNT -lt $TIMEOUT ]; do
    LASTSAVE=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)
    CURRENT_TIME=$(date +%s)
    
    if [ "$((CURRENT_TIME - LASTSAVE))" -lt 2 ]; then
        echo "✓ Save completed"
        break
    fi
    
    sleep 1
    COUNT=$((COUNT + 1))
done

if [ $COUNT -eq $TIMEOUT ]; then
    echo "⚠ Save did not complete within timeout"
fi

# Copy RDB file from Docker container
if [ -n "$DOCKER_CONTAINER" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/redis_$TIMESTAMP.rdb"
    
    echo "Copying RDB file from Docker container..."
    if docker cp "$DOCKER_CONTAINER:/data/dump.rdb" "$BACKUP_FILE"; then
        # Compress
        gzip "$BACKUP_FILE"
        BACKUP_SIZE=$(du -h "$BACKUP_FILE.gz" | cut -f1)
        echo "✓ Backup completed - Size: $BACKUP_SIZE"
    else
        echo "✗ Failed to copy RDB file"
        exit 1
    fi
else
    echo "⚠ DOCKER_CONTAINER not set, skipping file copy"
fi

# Clean up old backups
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "redis_*.rdb.gz" -mtime +"$RETENTION_DAYS" -delete
echo "✓ Cleanup completed"

exit 0
