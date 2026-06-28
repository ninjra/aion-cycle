#!/usr/bin/env bash
# Install the AION proof toolchain locally. Idempotent.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

echo "[setup] node: $(command -v node || echo MISSING)"
command -v node >/dev/null || { echo "node >= 18 is required"; exit 1; }

echo "[setup] installing locked node dependencies"
npm ci --prefix "$ROOT" --cache "$HOME/.cache/aion-npm"
SNARKJS="$ROOT/node_modules/.bin/snarkjs"
[ -x "$SNARKJS" ] || { echo "local snarkjs missing after npm ci"; exit 1; }
echo "[setup] snarkjs: $SNARKJS"

if ! command -v circom >/dev/null; then
  echo "[setup] fetching circom prebuilt binary"
  url="https://github.com/iden3/circom/releases/download/v2.2.3/circom-linux-amd64"
  curl -fsSL "$url" -o "$BIN/circom"
  chmod +x "$BIN/circom"
  echo "85342c7ff332d948df7c0c50ecf201e6129349aef550ce873f3c811b79fe53a3  $BIN/circom" | sha256sum -c -
  echo "[setup] installed circom to $BIN/circom (ensure $BIN is on PATH)"
fi
CIRCOM_PATH="$(command -v circom || echo "$BIN/circom")"
echo "[setup] circom: $CIRCOM_PATH"
echo "85342c7ff332d948df7c0c50ecf201e6129349aef550ce873f3c811b79fe53a3  $CIRCOM_PATH" | sha256sum -c -

PTAU="$ROOT/powersOfTau28_hez_final_18.ptau"
PTAU_SHA256="e970efa7774da80101e0ac336d083ef3339855c98112539338d706b2b89ac694"
if [ ! -f "$PTAU" ]; then
  echo "[setup] fetching powers of tau (2^18)"
  curl -fsSL "https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_18.ptau" -o "$PTAU"
fi
echo "[setup] hash-checking powers of tau"
echo "$PTAU_SHA256  $PTAU" | sha256sum -c -
if [ "${AION_VERIFY_PTAU:-0}" = "1" ]; then
  echo "[setup] structurally verifying powers of tau (slow)"
  "$SNARKJS" powersoftau verify "$PTAU"
else
  echo "[setup] skipped structural ptau verify (set AION_VERIFY_PTAU=1 or run make verify-ptau)"
fi

echo "[setup] done. Run: python3 aion_cycle.py"
