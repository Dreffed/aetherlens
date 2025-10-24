#!/bin/bash
# Configure PostgreSQL authentication
# This script runs before database initialization

set -e

# Update pg_hba.conf to require md5 password authentication for all connections
cat >> "$PGDATA/pg_hba.conf" <<EOF

# AetherLens: Require password authentication for all connections
host all all all md5
EOF

echo "PostgreSQL authentication configured for md5 passwords"
