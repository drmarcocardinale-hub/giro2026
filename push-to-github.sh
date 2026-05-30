#!/bin/bash
# ============================================================
# Giro 2026 Dashboard — Push to GitHub (run once)
# ============================================================
# Prerequisites:
#   - git installed
#   - GitHub account: drmarcocardinale-hub
#   - Repo "giro2026" created at github.com/drmarcocardinale-hub/giro2026
#     (create it empty — no README, no .gitignore)
# ============================================================

set -e

REPO="https://github.com/drmarcocardinale-hub/giro2026.git"

echo "🚴 Giro 2026 Dashboard — GitHub Push Script"
echo "============================================"
echo "Repo: $REPO"
echo ""

# Init git if not already done
if [ ! -d ".git" ]; then
  git init
  echo "✅ git init done"
fi

# Stage all files
git add .
git status

echo ""
echo "📦 Committing..."
git commit -m "🚴 Giro d'Italia 2026 dashboard — initial push" || echo "(nothing new to commit)"

# Set branch to main
git branch -M main

# Add remote (ignore if already set)
git remote add origin "$REPO" 2>/dev/null || git remote set-url origin "$REPO"

echo ""
echo "🚀 Pushing to GitHub..."
echo "   (You will be prompted for GitHub credentials if not cached)"
git push -u origin main

echo ""
echo "✅ Done! Now:"
echo "   1. Go to https://github.com/drmarcocardinale-hub/giro2026/settings/pages"
echo "   2. Set Source = 'Deploy from branch' → main → / (root)"
echo "   3. Click Save"
echo "   4. Wait ~60 seconds"
echo "   5. Visit: https://drmarcocardinale-hub.github.io/giro2026/"
