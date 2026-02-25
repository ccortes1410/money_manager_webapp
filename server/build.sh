#!/usr/bin/env bash
# build.sh - Render runs this during deployment

set -o errexit

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt 

echo "=== Installing system dependencies for mysqlclient ==="
# Render uses Ubuntu, install MySQL dev libraries
apt-get update && apt-get install -y default-libmysqlclient-dev build-essential pkg-config || true

echo "=== Installing Node and building React ==="
cd frontend

# Clean install — remove old node_modules completely
rm -rf node_modules
rm -rf package-lock.json          # Remove lock file to force fresh resolution
npm cache clean --force            # Clear npm cache
npm install
chmod +x node_modules/.bin/react-scripts

CI=false npm run build
cd ..

echo "=== Collecting static files ==="
python manage.py collectstatic --no-input

echo "=== Running database migrations ==="
python manage.py migrate

echo "=== Build complete ==="