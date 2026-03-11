# MenuRival

MenuRival is a restaurant menu benchmarking tool that lets operators compare their pricing against up to 9 competitors across standardized dish categories. It ingests menus via URL scraping or photo/PDF upload, uses Claude AI to parse and standardize items, and generates actionable pricing insights.

## Setup

```bash
# 1. Clone and enter the repo
git clone https://github.com/louispetauton/MenuRival.git
cd MenuRival

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
playwright install chromium

# 5. Copy and fill in environment variables
cp .env.example .env
# Edit .env and fill in:
#   SUPABASE_URL — from your Supabase project settings
#   SUPABASE_SERVICE_KEY — service role key from Supabase
#   ANTHROPIC_API_KEY — from console.anthropic.com

# 6. Deploy the database schema
# Open db/schema.sql, copy the contents, paste into your
# Supabase SQL Editor → Run
```

## Local Development

Run the API and frontend in two terminals:

```bash
# Terminal 1 — API (from repo root, venv activated)
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd dashboard
npm install
npm run dev
```

Open http://localhost:5173 in your browser.
The frontend proxies /api → http://localhost:8000.

## Replit Deployment

1. Fork or import this repo into Replit
2. In Replit Secrets, add:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `ANTHROPIC_API_KEY`
3. Click **Run** — `start.sh` handles everything automatically

## The 4-Stage Workflow

**1. Intake** — Paste up to 10 restaurant URLs (website, Yelp, or Google Maps). Claude auto-extracts the name, address, neighborhood, cuisine, and star ratings. Then upload menus per meal type (breakfast, lunch, dinner, etc.) as PDFs or images — Claude Vision parses every item and price.

**2. Standardization** — Click "Run Standardization" and Claude maps every raw menu item to a canonical name and category (e.g. "Grass-Fed Smash Burger" → Burger). This enables apples-to-apples comparison across restaurants.

**3. Comparison Dashboard** — Browse category tabs (Burger, Salad, Pasta, etc.) to see a price ranking table. Your subject restaurant is highlighted in indigo. Ranks show who's cheapest to most expensive within each category.

**4. Insight Commentary** — Click "Generate Insight" and Claude writes a benchmarking brief for your subject restaurant: pricing position, opportunities (specific dishes where you could raise prices), and category gaps (what competitors offer that you don't).
