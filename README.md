# 🚴 Giro d'Italia 2026 — Live Dashboard

Interactive race dashboard built by **Dr Marco Cardinale** — hosted on GitHub Pages with automatic daily data updates.

🔗 **Live site:** https://drmarcocardinale-hub.github.io/giro2026/

## Features

- 📊 Live GC standings & evolution chart
- 🏁 Stage-by-stage results for all 21 stages
- 💜 Points classification (Magnier vs Narváez battle)
- 👤 Rider profiles — age, height, weight, Grand Tour experience
- ⚡ Estimated power output data (model-based, clearly labelled)
- 📝 WordPress embed code & blog snippet generator

## Auto-Update

A **GitHub Actions** workflow runs every evening at 20:00 UTC. It:
1. Scrapes [CyclingStage.com](https://www.cyclingstage.com) for new stage results
2. Updates `data.json` with the latest winner, GC, and points data
3. Generates a fresh `blog-snippet.md` ready to paste into WordPress
4. Commits and pushes if anything changed

## Files

| File | Purpose |
|------|---------|
| `index.html` | Interactive dashboard (reads `data.json` at load time) |
| `data.json` | Race data — updated automatically each evening |
| `scraper.py` | Python scraper run by GitHub Actions |
| `blog-snippet.md` | Auto-generated WordPress blog post (updated daily) |
| `.github/workflows/update-daily.yml` | GitHub Actions schedule |

## Setup (one time)

```bash
# 1. Create repo "giro2026" on github.com/drmarcocardinale-hub
# 2. Run these commands in this folder:
git init
git add .
git commit -m "🚴 Initial Giro 2026 dashboard"
git branch -M main
git remote add origin https://github.com/drmarcocardinale-hub/giro2026.git
git push -u origin main
```

Then go to **GitHub → Settings → Pages → Source: Deploy from branch → main / root** and save.

Your dashboard will be live at:  
`https://drmarcocardinale-hub.github.io/giro2026/`

## WordPress Embed

Add a **Custom HTML** block in any post:

```html
<iframe
  src="https://drmarcocardinale-hub.github.io/giro2026/"
  width="100%" height="900"
  style="border:none;border-radius:12px;"
  loading="lazy"
  title="Giro d'Italia 2026 Dashboard">
</iframe>
```

Or use the daily `blog-snippet.md` as a ready-to-paste markdown post.

---
Data sourced from [CyclingStage.com](https://www.cyclingstage.com). Power estimates are model-based, not telemetry.
