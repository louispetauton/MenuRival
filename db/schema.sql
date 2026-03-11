-- ============================================================
-- MenuRival Schema
-- Deploy this by pasting into Supabase SQL Editor → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS markets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  slug text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now()
);

INSERT INTO markets (name, slug) VALUES ('San Francisco', 'sf')
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS restaurants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  market_id uuid REFERENCES markets(id),
  name text NOT NULL,
  slug text UNIQUE,
  address text,
  neighborhood text,
  phone text,
  website_url text,
  cuisine_type text[],
  google_stars numeric(2,1),
  yelp_stars numeric(2,1),
  is_subject boolean DEFAULT false,
  intake_status text DEFAULT 'pending',
  -- pending | active | archived
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS menu_pulls (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  restaurant_id uuid REFERENCES restaurants(id) ON DELETE CASCADE,
  menu_type text DEFAULT 'unknown',
  -- breakfast | brunch | lunch | dinner | drinks | happy_hour | tasting_menu | unknown
  source text,
  source_url text,
  parse_status text DEFAULT 'pending',
  -- pending | success | failed
  item_count integer DEFAULT 0,
  raw_content text,
  model_used text,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS menu_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  restaurant_id uuid REFERENCES restaurants(id) ON DELETE CASCADE,
  pull_id uuid REFERENCES menu_pulls(id) ON DELETE CASCADE,
  menu_type text,
  name text NOT NULL,
  description text,
  price numeric(8,2),
  price_notes text,
  category text,
  standardized_name text,
  standardized_category text,
  confidence text,
  -- high | medium | low
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS standardized_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name text NOT NULL,
  category text NOT NULL,
  item_count integer DEFAULT 1,
  example_raw_names text[],
  first_seen_at timestamptz DEFAULT now(),
  last_updated_at timestamptz DEFAULT now(),
  UNIQUE(canonical_name, category)
);

CREATE TABLE IF NOT EXISTS insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  subject_restaurant_id uuid REFERENCES restaurants(id) ON DELETE CASCADE,
  headline text,
  pricing_position text,
  opportunities jsonb,
  gaps jsonb,
  raw_response text,
  date_generated timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_standardized ON menu_items(standardized_category);
CREATE INDEX IF NOT EXISTS idx_menu_pulls_restaurant ON menu_pulls(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_restaurants_subject ON restaurants(is_subject);

-- END OF SCHEMA
-- After running this, add your Supabase URL and service key to .env
