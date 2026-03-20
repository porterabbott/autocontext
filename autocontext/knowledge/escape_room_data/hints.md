# Escape Room Data — Accumulated Knowledge

## The Core Problem (as of March 2026)
Evidence/request ratio has collapsed from healthy (5.0+) to critical (0.01-0.5).
The pipeline is spending HTTP budget re-scraping unchanged pages and hitting
broken extractors. Coverage metrics are stalling.

## What's Actually Broken

### Bookeo Deep Extractor
- `scripts/adapters/bookeo.py` has been returning empty stdout for weeks
- Every run reports "0/N empty stdout failures" but nobody fixes it
- This blocks room/pricing extraction for all Bookeo-powered locations
- **FIX THIS BEFORE SCALING THROUGHPUT**

### Reviews
- `collect_reviews.py` hangs without a hard timeout
- When it hangs, it gets SIGTERM'd, wasting the entire review budget
- Needs a per-location timeout wrapper

### Stealth Budget
- Currently capped at 25 fetches per run
- After 25 stealth fetches, all remaining domains that need stealth are skipped
- This means 50-70 locations get domain-skipped every run
- Consider: raise the budget, or implement domain-error suppression so known-bad
  domains don't consume stealth slots

### Unchanged Pages
- HEAD-first change detection exists but pages still get fully fetched even when
  ETag/Last-Modified indicate no change
- These unchanged fetches consume the --limit budget but produce zero evidence
- Need skip logic for consecutive unchanged patterns

## What Works Well
- FareHarbor deep extractor: 6/7+ success rate consistently
- Peek deep extractor: reliable
- Checkfront: reliable
- Canonical apply + replay integrity: rock solid (100% replay for weeks)
- Status derivation: clean
- Trust metrics: stable

## Full Tool Stack

### Pipeline Scripts (run via `.venv/bin/python3 scripts/<name>.py`)
- `enrich_location.py` — main enrichment engine (args: --limit N --delay N --depth 1|2 --cadence tiered)
- `collect_reviews.py` — Google Maps review scraping (arg: --limit N)
- `geocode_locations.py` — Nominatim geocoding for lat/lng
- `date_locations.py` — year-opened estimation via web evidence
- `apply_canonical_selection.py` — promote best evidence to canonical fields
- `derive_status.py` — compute open/closed/likely_open status
- `score_volatility.py` — recalculate volatility scores for scheduling priority
- `stats.py` — current coverage snapshot (run this first every time)
- `last_run.py` — structured summary of the most recent run
- `llm_extract.py` — LLM-powered room/pricing extraction from HTML

### Deep Extractors (`scripts/adapters/`)
These extract rooms, pricing, and booking data from specific booking engines:
- `bookeo.py` — **CURRENTLY BROKEN** (empty stdout for weeks)
- `fareharbor.py` — reliable (6/7+ success rate)
- `peek.py` — reliable
- `checkfront.py` — reliable
- `xola.py` — works
- `resova.py` — works
- `buzzshot.py` — works
- `offthecouch.py` — works
- `paniq.py` — has unmapped slug issues
- `teg.py` — The Escape Game specific

### Web Scraping / Fetching Tools (available on PATH)
- `searx` — SearXNG search CLI: `searx "query" -n 10`
- `scrape` — web scraper toolkit:
  - `scrape fetch URL --format markdown`
  - `scrape search "query" -n 10`
  - `scrape deep "query" -n 5` (search + fetch results)
  - `scrape batch URL1 URL2` (parallel fetch)
- `stealth-fetch` — Scrapling-based Cloudflare bypass:
  - `stealth-fetch URL --format text`
  - `stealth-fetch URL --proxy` (adds Decodo residential proxy)
  - `stealth-fetch URL --fetcher dynamic` (Playwright Chromium)
- `agent-browser` — headless Chrome CLI for JS-rendered pages:
  - `agent-browser open URL` → `agent-browser snapshot` → `agent-browser get text "selector"`
  - `agent-browser click @ref` / `agent-browser fill @ref "text"`
  - `agent-browser close` (always close when done!)
  - Good for: interactive booking pages, SPAs, multi-step navigation
  - Bad for: DataDome-protected sites (use cf-render instead)
- `cf-render` — Cloudflare Browser Rendering API (10hr/month quota):
  - `cf-render URL --format text --max-chars 5000`
  - `cf-render URL --screenshot --output file.png`
  - Last resort for heavily protected sites — conserve quota
- `web_fetch` — basic URL fetch (OpenClaw built-in)

### Tool Escalation Order (for scraping)
1. Direct Python fetch (requests/httpx) — fastest, used by enrichment pipeline
2. `scrape fetch` / `web_fetch` — simple URL fetch with readability extraction
3. `stealth-fetch` — for Cloudflare/bot-detected sites
4. `stealth-fetch --proxy` — adds residential IP rotation
5. `agent-browser` — for JS-rendered pages needing interaction
6. `cf-render` — nuclear option for DataDome/heavy protection (quota-limited)

### Proxies
- **Decodo Residential Proxy** (US sticky session): available via `stealth-fetch --proxy`
  - Credentials in `~/.env.secrets` as `SCRAPE_PROXY_URL`
  - Endpoint: `us.decodo.com:10001` (sticky session for consistent IP)
  - Usage is metered — use only when direct + stealth fetch both fail
  - Best for: sites that block datacenter IPs even after Cloudflare bypass
- **Cloudflare Browser Rendering**: `cf-render` CLI (see above)
  - 10 hours/month free quota — use sparingly
  - Credentials in `~/.env.secrets`: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`
  - Best for: DataDome, heavy Cloudflare protection, TripAdvisor-class blocking

### Database
- SQLite at `data/escape_rooms.db`
- Key tables: `locations`, `entities`, `rooms`, `evidence`, `field_changes`,
  `scrape_log`, `reviews`, `companies`
- NEVER modify the schema — only read/write data through the scripts
- Can query directly for diagnostics: `.venv/bin/python3 -c "import sqlite3; ..."`

### Git
- Commit changes to `meta/strategy.md` after every run
- Use conventional commits: `chore:`, `fix:`, `feat:`

## Strategy Anti-Patterns
- Running the same --limit 150 --depth 2 for 10+ consecutive runs without
  investigating WHY yield is low
- Writing "next run should try X" in strategy.md but then not doing X
- Skipping reviews because they "hung last time" without adding a timeout
- Reducing --limit when the problem is broken extractors, not throughput
- Treating evidence/request < 0.5 as acceptable

## Coverage Gaps Worth Targeting
- Phone: 38.9% — many sites have phone numbers that aren't being extracted
- Pricing: 34.4% — pricing extractors exist but many sites aren't deep-crawled
- Reviews: 32.2% — review collection is unreliable
- Coordinates: 66.7% — geocoding works but is gated by threshold
- Rooms with difficulty: 1.3% — barely scraped
- Rooms with pricing: 10.9% — deep extractors could improve this dramatically
