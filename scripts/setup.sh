#!/usr/bin/env bash
# Install the AION proof toolchain locally. Idempotent.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$HOME/.local/bin"
mkdir -p "$BIN"

echo "[setup] node: $(command -v node || echo MISSING)"
command -v node >/dev/null || { echo "node >= 18 is required"; exit 1; }

if ! command -v snarkjs >/dev/null; then
  echo "[setup] installing snarkjs (user prefix, dedicated cache)"
  npm install -g snarkjs@0.7.6 --prefix "$HOME/.local" --cache "$HOME/.cache/aion-npm"
fi
echo "[setup] snarkjs: $(command -v snarkjs || echo MISSING)"

echo "[setup] installing circomlib"
npm install circomlib@2.0.5 --prefix "$ROOT" --cache "$HOME/.cache/aion-npm"

if ! command -v circom >/dev/null; then
  echo "[setup] fetching circom prebuilt binary"
  url="https://github.com/iden3/circom/releases/download/v2.2.3/circom-linux-amd64"
  curl -fsSL "$url" -o "$BIN/circom"
  chmod +x "$BIN/circom"
  echo "[setup] installed circom to $BIN/circom (ensure $BIN is on PATH)"
fi
echo "[setup] circom: $(command -v circom || echo "$BIN/circom")"

PTAU="$ROOT/powersOfTau28_hez_final_17.ptau"
if [ ! -f "$PTAU" ]; then
  echo "[setup] fetching powers of tau (2^10)"
  curl -fsSL "https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_17.ptau" -o "$PTAU"
fi
echo "[setup] verifying powers of tau"
snarkjs powersoftau verify "$PTAU"

echo "[setup] done. Run: python3 aion_cycle.py"
