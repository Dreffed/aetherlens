#!/bin/bash
# AetherLens Database Backup Script
# Creates compressed backups of the TimescaleDB database

set -e

# Configuration
BACKUP_DIR=${BACKUP_DIR:-./backups}
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=${DB_NAME:-aetherlens}
DB_USER=${DB_USER:-postgres}
DB_CONTAINER=${DB_CONTAINER:-aetherlens-db}
KEEP_BACKUPS=${KEEP_BACKUPS:-7}

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "========================================="
echo "AetherLens Database Backup"
echo "========================================="
echo "Date: $(date)"
echo "Database: $DB_NAME"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Create compressed backup
echo "[1/3] Creating compressed backup..."
docker exec $DB_CONTAINER pg_dump -U $DB_USER -F c -b -v \
  $DB_NAME > "$BACKUP_DIR/aetherlens_$DATE.backup" 2>&1 | grep -v "^$"

BACKUP_FILE="$BACKUP_DIR/aetherlens_$DATE.backup"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "✅ Backup created: $BACKUP_FILE ($BACKUP_SIZE)"

# Create plain SQL backup (human-readable)
echo ""
echo "[2/3] Creating SQL backup (human-readable)..."
docker exec $DB_CONTAINER pg_dump -U $DB_USER \
  $DB_NAME | gzip > "$BACKUP_DIR/aetherlens_$DATE.sql.gz"

SQL_SIZE=$(du -h "$BACKUP_DIR/aetherlens_$DATE.sql.gz" | cut -f1)
echo "✅ SQL backup created: aetherlens_$DATE.sql.gz ($SQL_SIZE)"

# Cleanup old backups
echo ""
echo "[3/3] Cleaning up old backups (keeping last $KEEP_BACKUPS)..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/aetherlens_*.backup 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$KEEP_BACKUPS" ]; then
    ls -t "$BACKUP_DIR"/aetherlens_*.backup | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
    ls -t "$BACKUP_DIR"/aetherlens_*.sql.gz | tail -n +$((KEEP_BACKUPS + 1)) | xargs rm -f
    echo "✅ Cleaned up old backups"
else
    echo "ℹ️  No cleanup needed (total backups: $BACKUP_COUNT)"
fi

echo ""
echo "========================================="
echo "Backup completed successfully!"
echo "========================================="
echo "Backup files:"
echo "  - $BACKUP_FILE"
echo "  - $BACKUP_DIR/aetherlens_$DATE.sql.gz"
echo ""
echo "To restore:"
echo "  ./scripts/restore_database.sh $BACKUP_FILE"
