#!/usr/bin/env python3
"""
Giro d'Italia 2026 — Daily Data Scraper
Runs via GitHub Actions each evening to fetch latest results from CyclingStage.com
and update data.json for the GitHub Pages dashboard.
"""

import json
import re
import sys
import urllib.request
from datetime import date, datetime

DATA_FILE = "data.json"
BASE_URL = "https://www.cyclingstage.com"

STAGE_URLS = {
    19: "/giro-2026-results/stage-19-italy-results-2026/",
    20: "/giro-2026-results/stage-20-italy-results-2026/",
    21: "/giro-2026-results/stage-21-italy-results-2026/",
}

POINTS_URLS = {
    19: "/giro-2026-points-classification/stage-19-italy-ciclamino-2026/",
    20: "/giro-2026-points-classification/stage-20-italy-ciclamino-2026/",
    21: "/giro-2026-points-classification/stage-21-italy-ciclamino-2026/",
}

# Fallback GC data (populated from known sources; scraper augments this)
STAGE_DATES = {
    19: "2026-05-29", 20: "2026-05-30", 21: "2026-05-31"
}


def fetch(url: str) -> str:
    """Fetch a URL and return the text content."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GiroDashboard/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠ Fetch failed for {url}: {e}", file=sys.stderr)
        return ""


def parse_stage_results(html: str, stage_n: int) -> dict | None:
    """Extract stage winner, GC leader, and top-10 from HTML."""
    if not html:
        return None

    # Stage winner from h2 "Stage N Results"
    winner_block = re.search(
        r"Stage \d+ Results.*?1\.\s+([^\(]+)\(([a-z]{3})\)\s+([\d:]+)",
        html, re.DOTALL | re.IGNORECASE
    )
    if not winner_block:
        return None

    winner_name = winner_block.group(1).strip()
    winner_time = winner_block.group(3).strip()

    # Extract top-10
    top10_block = re.search(
        r"Stage \d+ Results.*?GC after stage", html, re.DOTALL | re.IGNORECASE
    )
    top10 = []
    if top10_block:
        lines = re.findall(
            r"(\d+)\.\s+([^\(]+)\(([a-z]{3})\)\s+([\d:+s\.t]+)",
            top10_block.group(0), re.IGNORECASE
        )
        for pos, name, nat, time in lines[:10]:
            top10.append({"pos": int(pos), "rider": name.strip(), "nat": nat, "time": time.strip()})

    # Extract GC leader after stage
    gc_block = re.search(
        r"GC after stage \d+(.*?)Race report",
        html, re.DOTALL | re.IGNORECASE
    )
    gc_leader = ""
    gc_top5 = []
    if gc_block:
        gc_lines = re.findall(
            r"(\d+)\.\s+([^\(]+)\(([a-z]{3})\)(?:\s*\+\s*([\d:]+))?",
            gc_block.group(1), re.IGNORECASE
        )
        for pos, name, nat, gap in gc_lines[:5]:
            if int(pos) == 1:
                gc_leader = name.strip()
            gc_top5.append({"pos": int(pos), "rider": name.strip(), "gap": f"+{gap}" if gap else "Leader"})

    # Try to extract avg speed from page text
    speed_match = re.search(r"average speed.*?([\d.]+)\s*km", html, re.IGNORECASE)
    avg_speed = float(speed_match.group(1)) if speed_match else None

    return {
        "winner": winner_name,
        "winnerTime": winner_time,
        "gcLeader": gc_leader,
        "gcTop5": gc_top5,
        "top10": top10,
        "avgSpeed": avg_speed,
    }


def update_data(data: dict) -> bool:
    """Check for new stage results and update data.json. Returns True if updated."""
    updated = False
    today = date.today().isoformat()
    completed = data["race"]["completedStages"]
    total = data["race"]["totalStages"]

    print(f"📅 Today: {today}")
    print(f"📊 Currently {completed}/{total} stages complete")

    for stage in data["stages"]:
        n = stage["n"]
        if stage["winner"] is not None:
            continue  # Already have this stage
        if stage["date"] > today:
            print(f"  ⏭  Stage {n} ({stage['date']}) not yet raced — skipping")
            continue

        url = BASE_URL + STAGE_URLS.get(n, f"/giro-2026-results/stage-{n}-italy-results-2026/")
        print(f"  🔍 Fetching Stage {n}: {url}")
        html = fetch(url)
        result = parse_stage_results(html, n)

        if result and result.get("winner"):
            stage["winner"] = result["winner"]
            stage["winTeam"] = ""  # Hard to parse reliably; leave blank
            stage["gcLeader"] = result.get("gcLeader", "")
            if result.get("avgSpeed"):
                stage["avgSpeed"] = result["avgSpeed"]

            print(f"  ✅ Stage {n} winner: {result['winner']}")
            data["race"]["completedStages"] = max(completed, n)
            completed = data["race"]["completedStages"]

            # Update GC if we got gc data
            if result.get("gcTop5"):
                _merge_gc(data, result["gcTop5"])

            updated = True
        else:
            print(f"  ℹ  Stage {n}: no result found yet")

    data["race"]["lastUpdated"] = today
    return updated


def _merge_gc(data: dict, gc_top5: list):
    """Merge scraped GC top-5 into existing GC data."""
    existing = {r["rider"]: r for r in data["gc"]}
    for item in gc_top5:
        name = item["rider"]
        if name in existing:
            existing[name]["timeGap"] = item["gap"]
        else:
            data["gc"].append({
                "pos": item["pos"], "rider": name, "team": "", "nat": "",
                "timeGap": item["gap"], "timeGapSec": 0
            })
    data["gc"].sort(key=lambda x: x["pos"])
    if data["gc"]:
        data["gcLeader"]["name"] = data["gc"][0]["rider"]


def generate_blog_snippet(data: dict) -> str:
    """Generate a markdown blog post snippet for the latest completed stage."""
    completed = data["race"]["completedStages"]
    if completed == 0:
        return "No stages completed yet."

    stage = next((s for s in data["stages"] if s["n"] == completed), None)
    if not stage:
        return ""

    gc = data["gc"]
    gc1 = gc[0] if gc else {}
    gc2 = gc[1] if len(gc) > 1 else {}
    gc3 = gc[2] if len(gc) > 2 else {}

    today = datetime.now().strftime("%B %d, %Y")

    snippet = f"""## 🚴 Giro d'Italia 2026 — Stage {completed} Update ({today})

**Stage {completed}:** {stage['start']} → {stage['end']} ({stage.get('dist','?')} km · {stage['type'].upper()})

**Winner:** {stage.get('winner','TBC')} ({stage.get('winTeam','')})

### 🌸 General Classification (after Stage {completed})
| Pos | Rider | Team | Gap |
|-----|-------|------|-----|
| 1 | **{gc1.get('rider','')}** {gc1.get('nat','')} | {gc1.get('team','')} | Leader |
| 2 | {gc2.get('rider','')} {gc2.get('nat','')} | {gc2.get('team','')} | {gc2.get('timeGap','')} |
| 3 | {gc3.get('rider','')} {gc3.get('nat','')} | {gc3.get('team','')} | {gc3.get('timeGap','')} |

### 💜 Points Classification
**Leader: {data['pointsLeader']['name']}** ({data['pointsLeader']['team']})

---
📊 [View the full interactive dashboard](https://drmarcocardinale-hub.github.io/giro2026/)

*Data updated automatically each evening. Power estimates are modelled values, not telemetry.*
"""
    return snippet


def main():
    print("🚴 Giro d'Italia 2026 — Daily Scraper")
    print("=" * 45)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {DATA_FILE} not found", file=sys.stderr)
        sys.exit(1)

    updated = update_data(data)

    if updated:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n✅ {DATA_FILE} updated successfully")
    else:
        print("\nℹ  No new data — nothing to update")

    # Always write the blog snippet for today
    snippet = generate_blog_snippet(data)
    with open("blog-snippet.md", "w", encoding="utf-8") as f:
        f.write(snippet)
    print("📝 blog-snippet.md written")

    # Exit code 0 = success (GitHub Actions will commit if files changed)
    sys.exit(0)


if __name__ == "__main__":
    main()
