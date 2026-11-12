#!/bin/zsh
# Publish the devlog to https://github.com/AtlantisPleb/SpliceDevLog.
# Copies docs/devlog (entries, media, process docs) plus the scripts and docs the
# entries link to (under code/), then commits and pushes.
#
# Usage: tools/devlog/publish.sh "commit message"
# Clone location: $SPLICE_DEVLOG_DIR, default ~/games/SpliceDevLog.
set -e
ROOT=${0:a:h:h:h}
DEST=${SPLICE_DEVLOG_DIR:-$HOME/games/SpliceDevLog}
MSG=${1:-"Update devlog"}

[ -d "$DEST/.git" ] || git clone https://github.com/AtlantisPleb/SpliceDevLog.git "$DEST"
git -C "$DEST" pull --ff-only -q 2>/dev/null || true

# Devlog content mirrors docs/devlog at the repo root.
rsync -a --delete --exclude .git --exclude code "$ROOT/docs/devlog/" "$DEST/"
# Code and docs the entries link to.
mkdir -p "$DEST/code/tools" "$DEST/code/docs/art"
rsync -a --delete "$ROOT/tools/" "$DEST/code/tools/"
cp "$ROOT/docs/art/moebius-style-spec.md" "$DEST/code/docs/art/"

# Every link to the published repo must point at a file that exists in it.
missing=0
for url in $(grep -rhoE 'https://(raw\.githubusercontent\.com/AtlantisPleb/SpliceDevLog/main|github\.com/AtlantisPleb/SpliceDevLog/blob/main)/[^) ]+' "$DEST" --include='*.md' | sort -u); do
  rel=${url#*SpliceDevLog/main/}; rel=${rel#*SpliceDevLog/blob/main/}
  [[ "$rel" == *NNNN* || "$rel" == *...* ]] && continue
  [ -e "$DEST/$rel" ] || { echo "missing: $rel" >&2; missing=1; }
done
[ $missing -eq 0 ] || { echo "Fix the missing files before publishing." >&2; exit 1; }

cd "$DEST"
git add -A
if git diff --cached --quiet; then echo "Nothing to publish."; exit 0; fi
git commit -q -m "$MSG"
git branch -M main
git push -q -u origin main
echo "Published: https://github.com/AtlantisPleb/SpliceDevLog"
