# Deep Research Hints

Seeded from `meta/strategy.md` → **What's Working**, plus critical operating constraints.

## Working Patterns

- Use **primary-source archives** (season stat pages, official bios, original coverage) to expand first-degree connections when person-name search quality collapses.
- Pivot from **snippet-discovered direct URLs** (especially canonical article IDs/slugs), then fetch the page directly instead of repeating broad SERP queries.
- Run **low-volume DuckDuckGo/HTML-style pivots** to surface direct URLs when SearX relevance degrades.
- Prefer **quoted phrase + location/context pivots** to recover independent corroboration when direct outlet links are dead.
- Use **multi-name cluster queries** (known associates together) to discover long-tail pages that confirm relationship edges.
- Revisit known high-value sources with tighter terms; **targeted re-fetching** often reveals missed quantitative details.
- Use **Cannon Courier direct article URLs** and readability extraction for class/year and roster-level details.
- Treat **ESPN profiles and official athletics pages** as useful corroboration for biographical anchors (e.g., birthplace, season participation).
- Mine **social cross-post paths** around known interviews/articles for additional names, timeline breadcrumbs, and org links.
- Keep people-data directories as **lead generators only**; promote claims to stable facts only after primary-source corroboration.

## Critical Constraints & Tooling Guidance

- **SearX/Bing results are often irrelevant** — prefer Google and DuckDuckGo engines when possible.
- **LinkedIn profile pages are blocked**, but LinkedIn **activity URLs** can still leak useful outward-link context.
- **Direct URL fetches (`web_fetch`) often succeed** where search-based flows fail.
- Use **`cf-render` as the nuclear option** for Cloudflare-protected sites; conserve the 10 hr/month quota.
- **Never attempt automated logins** — research must stay public and unauthenticated.
- **`scrape deep` combines search + fetch** and is usually the fastest exploratory pass.
- **TNBEAR is frequently down**; note outage quickly and move on instead of burning query budget.

## Browser Automation (agent-browser)

The `agent-browser` CLI provides headless Chrome automation from any shell context:
```bash
agent-browser open URL                    # Navigate (launches Chrome if needed)
agent-browser snapshot                    # Get accessibility tree with refs
agent-browser click @e2                   # Click by ref from snapshot
agent-browser fill @e3 "search query"     # Fill input by ref
agent-browser get text "h1"               # Get text by CSS selector
agent-browser get text @e1                # Get text by ref
agent-browser screenshot page.png         # Screenshot
agent-browser screenshot --annotate       # Screenshot with numbered labels
agent-browser eval "document.title"       # Run JavaScript
agent-browser close                       # Close browser
```
- Uses its own Chrome for Testing (separate from Brave and the Chrome user profile)
- Best for: interactive pages that need JS rendering, clicking through multi-page flows, scraping SPAs
- Limitations: gets caught by DataDome/advanced bot detection (TripAdvisor). Use `cf-render` for those.
- Always `agent-browser close` when done to free resources.

## Practical Escalation Order

1. `searx` / `scrape search` / `scrape deep`
2. `web_fetch` / `scrape fetch`
3. `stealth-fetch` (optionally `--proxy`)
4. `agent-browser` (for JS-rendered pages needing interaction)
5. `cf-render` (nuclear option for Cloudflare/DataDome-protected sites — conserve quota)
