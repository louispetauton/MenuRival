#!/bin/bash
set -e

echo "Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt -q

echo "Installing Node dependencies..."
cd dashboard
npm install -q
npm run build
cd ..

echo "Starting server..."
.venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 3000
