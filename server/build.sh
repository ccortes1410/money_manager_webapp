#!/usr/bin/env bash
# build.sh - Render runs this during deployment

set -o errexit

cd server

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt 

echo "=== Installing system dependencies for mysqlclient ==="
# Render uses Ubuntu, install MySQL dev libraries
apt-get update && apt-get install -y default-libmysqlclient-dev build-essential pkg-config || true

echo "=== Installing Node and building React ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Collecting static files ==="
python manage.py collectstatic --no-input

echo "=== Running database migrations ==="
python manage.py migrate

echo "=== Build complete ==="