#!/usr/bin/env bash
# GitNexus auto-refresh — re-index ONLY when source files changed since the
# last analyze. Wired as an async Stop hook in .claude/settings.local.json.
#
# "Changed" = any file under the repo with an mtime newer than the sentinel,
# excluding generated/churn dirs, the GitNexus index itself, .claude config,
# and CLAUDE.md (which `gitnexus analyze` rewrites on every run — would self-trigger).
set -u

REPO=/root/agentD
SENTINEL="$REPO/.gitnexus/.last_analyze"
LOG="$REPO/.gitnexus/analyze.log"
cd "$REPO" || exit 0

changed=1
if [ -e "$SENTINEL" ]; then
  hit=$(find . -type f -newer "$SENTINEL" \
        -not -path './.git/*' \
        -not -path './.gitnexus/*' \
        -not -path './.claude/*' \
        -not -path './venv/*' \
        -not -path './node_modules/*' \
        -not -path './.langgraph_api/*' \
        -not -path '*/__pycache__/*' \
        -not -path './.pytest_cache/*' \
        -not -path './sessions/*' \
        -not -name 'CLAUDE.md' \
        2>/dev/null | head -1)
  [ -z "$hit" ] && changed=0
fi

if [ "$changed" -eq 1 ]; then
  echo "[$(date -Iseconds)] changes detected -> gitnexus analyze" >> "$LOG"
  npx gitnexus analyze >> "$LOG" 2>&1 || true
  touch "$SENTINEL"
else
  echo "[$(date -Iseconds)] no source changes since last index -> skip" >> "$LOG"
fi
