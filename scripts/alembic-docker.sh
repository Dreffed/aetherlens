#!/bin/bash
# Run Alembic commands inside the Docker container
# Usage: ./scripts/alembic-docker.sh <alembic-command>
# Example: ./scripts/alembic-docker.sh current
# Example: ./scripts/alembic-docker.sh upgrade head

docker exec aetherlens-db sh -c "cd /docker-entrypoint-initdb.d/.. && alembic $*"
