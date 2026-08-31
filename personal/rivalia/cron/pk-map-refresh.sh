#!/bin/bash
# Weekly Rivalia PK-map refresh — publishes to GitHub Pages (personal repo Andre9670/rivalia-online).
#
# Pipeline (all local Python; scraping rivaliaonline.com is public, no auth needed):
#   1. build_seed.py          -> /tmp/all_players.json   (highscores seed, Aeternum world)
#   2. crawl_pk.py            -> /tmp/pk_profiles.json   (recursive crawl to closure)
#   3. build_pkdata.py        -> pk-map-data.json        (who-kills-who graph + danger scores)
#   3b. build_relationships.py -> relationships.json     (allies/enemies/co-faction ego-graph)
#   4. build_insights.py      -> insights-data.json      (loot/quests/farm/hunt areas)
#   5. INLINE=1 build_html.py -> ../../map/index.html    (self-contained, base64)
#   6. git commit + push      -> GitHub Pages republishes automatically
#
# The PK data lives INSIDE the reverse map as an in-page modal (button "PK Map"
# next to "Insights"). There is no separate PK-map html file.
#
# NOTE: build_pkdata.py / build_relationships.py filter to World==Aeternum
# (env PK_WORLD_FILTER, default Aeternum) — see personal/rivalia/NOTES.md.

set -u

# Resolve repo root from this script's location (personal/rivalia/cron/ -> repo root).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"      # personal/rivalia
ROOT="$(cd "$DIR/../.." && pwd)"                            # repo root
LOG="${LOG:-$DIR/cron-pk-map-refresh.log}"
echo "=== pk-map-refresh $(date -u +%FT%TZ) ===" >> "$LOG"

cd "$DIR" || { echo "  FATAL: no dir $DIR" >> "$LOG"; exit 1; }

# ---- 1-5. Scrape + build (all local Python) ----
{
  python3 build_seed.py          && \
  python3 crawl_pk.py            && \
  python3 build_pkdata.py        && \
  python3 build_relationships.py && \
  python3 build_insights.py      && \
  INLINE=1 python3 build_html.py
} >> "$LOG" 2>&1
RC=$?
if [ "$RC" != "0" ]; then
  echo "  FATAL: build pipeline failed (rc=$RC), not publishing — prior map/index.html kept" >> "$LOG"
  exit 1
fi

# ---- 6. Publish to GitHub Pages (commit the regenerated map + refreshed data) ----
cd "$ROOT" || { echo "  FATAL: no repo root $ROOT" >> "$LOG"; exit 1; }
git add map/index.html \
        personal/rivalia/pk-map-data.json \
        personal/rivalia/relationships.json \
        personal/rivalia/insights-data.json >> "$LOG" 2>&1
if git diff --cached --quiet; then
  echo "  [6] no changes to publish (map already up to date)" >> "$LOG"
else
  git commit -m "Weekly PK-map refresh $(date -u +%F)" >> "$LOG" 2>&1
  BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  for attempt in 1 2 3 4; do
    if git push origin "$BRANCH" >> "$LOG" 2>&1; then
      echo "  [6] pushed to $BRANCH — GitHub Pages will republish" >> "$LOG"; break
    fi
    wait=$((2 ** attempt)); echo "  [6] push failed, retry in ${wait}s" >> "$LOG"; sleep "$wait"
  done
fi
echo "=== pk-map-refresh done $(date -u +%FT%TZ) ===" >> "$LOG"
