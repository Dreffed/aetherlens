#!/bin/bash
# AetherLens Database Restore Script
# Restores database from a backup file

set -e

# Check if backup file provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Example:"
    echo "  $0 backups/aetherlens_20251024_140000.backup"
    echo ""
    echo "Available backups:"
    ls -lh backups/aetherlens_*.backup 2>/dev/null || echo "  No backups found in ./backups/"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME=${DB_NAME:-aetherlens}
DB_USER=${DB_USER:-postgres}
DB_CONTAINER=${DB_CONTAINER:-aetherlens-db}

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "========================================="
echo "AetherLens Database Restore"
echo "========================================="
echo "⚠️  WARNING: This will DROP and recreate the database!"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Database: $DB_NAME"
echo "Container: $DB_CONTAINER"
echo ""
read -p "Continue? (yes/no) " -r
echo ""

if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "[1/4] Terminating active connections..."
docker exec $DB_CONTAINER psql -U $DB_USER -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" \
    > /dev/null 2>&1 || true

echo "[2/4] Dropping existing database..."
docker exec $DB_CONTAINER dropdb -U $DB_USER --if-exists $DB_NAME

echo "[3/4] Creating fresh database..."
docker exec $DB_CONTAINER createdb -U $DB_USER $DB_NAME

echo "[4/4] Restoring from backup..."
cat "$BACKUP_FILE" | docker exec -i $DB_CONTAINER pg_restore -U $DB_USER -d $DB_NAME -v 2>&1 | \
    grep -E "(processing|creating|restoring)" || true

echo ""
echo "========================================="
echo "✅ Database restored successfully!"
echo "========================================="
echo ""

# Verify restoration
echo "Verifying restoration..."
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "\dt" | head -10
docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c \
    "SELECT COUNT(*) as device_count FROM devices; SELECT COUNT(*) as metric_count FROM metrics;" \
    2>/dev/null || true

echo ""
echo "Restore complete!"
