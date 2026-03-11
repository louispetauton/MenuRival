#!/bin/bash
set -e

echo "Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt -q

echo "Installing Playwright browser..."
PLAYWRIGHT_BROWSERS_PATH=/home/runner/.playwright-browsers \
  .venv/bin/playwright install chromium --with-deps 2>/dev/null || \
  .venv/bin/playwright install chromium

echo "Installing Node dependencies..."
cd dashboard
npm install -q
npm run build
cd ..

echo "Starting server..."
PLAYWRIGHT_BROWSERS_PATH=/home/runner/.playwright-browsers \
  .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 3000
