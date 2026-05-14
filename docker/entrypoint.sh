#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting Timely..."
exec python -m bot.main
