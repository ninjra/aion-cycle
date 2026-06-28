#!/usr/bin/env bash
# Non-destructive teaching demo: copy the committed bundle to a temp dir,
# tamper one statement field, and show that verification fails closed.
# The tracked working tree is never modified.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cp -r "$ROOT/." "$TMP/work" 2>/dev/null || { mkdir -p "$TMP/work"; (cd "$ROOT" && git ls-files && git ls-files --others --exclude-standard) | while read -r f; do mkdir -p "$TMP/work/$(dirname "$f")"; cp "$ROOT/$f" "$TMP/work/$f"; done; }

python3 - "$TMP/work/aion.statement.json" <<'PY'
import json, sys
p = sys.argv[1]
data = json.load(open(p))
data["proof_hash"] = "0" * 64  # tamper one field
json.dump(data, open(p, "w"), indent=2, sort_keys=True)
PY

echo "[break] tampered a copy of aion.statement.json (proof_hash) in a temp dir"
echo "[break] running verify on the tampered copy:"
out="$(cd "$TMP/work" && python3 aion_cycle.py --verify-statement aion.statement.json --explain 2>&1 || true)"
echo "$out"
echo "[break] the tracked repo was not modified; verify it still passes:"
( cd "$ROOT" && python3 aion_cycle.py --verify-statement aion.statement.json )
