#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_TRANSCRIPT_ROOT = "4fe55b20021791ebb3ca62b2773ea689e59deab6f68c3ecdea36ae37ab3a47a7"
PTAU = "powersOfTau28_hez_final_17.ptau"
ROOT = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT / "proofs" / "v1"
LENS = {"query": 30, "corpus0": 42, "corpus1": 33, "corpus2": 24, "emitted": 42}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def file_sha(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def receipt(kind: str, payload: dict[str, Any], children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    failed = list(payload.get("failed_checks") or [])
    child_hashes = [c["receipt_hash"] for c in children or []]
    if any(c.get("proof_passed") is not True for c in children or []):
        failed.append("child_failed")
    body = {"schema_version": f"aion-{kind}-receipt-v1", **payload, "child_receipt_hashes": child_hashes}
    body["failed_checks"] = failed
    body["proof_passed"] = not failed
    body["receipt_hash"] = sha256_hex(canonical_bytes(body))
    return body


def bits_le(value: int, width: int) -> list[str]:
    return [str((int(value) >> i) & 1) for i in range(width)]


def inv_or_zero(diff: int) -> str:
    p = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    v = int(diff) % p
    return "0" if v == 0 else str(pow(v, -1, p))


def select_winner(query: bytes, corpus: list[bytes]) -> int:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    if scores.count(max(scores)) != 1:
        raise RuntimeError("ambiguous_or_no_winner")
    return max(range(len(scores)), key=lambda i: scores[i])


def build_input(query: bytes, corpus: list[bytes], emitted: bytes, digest_hex: str) -> dict[str, Any]:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    if scores[0] <= scores[1] or scores[0] <= scores[2]:
        raise RuntimeError("winner_not_corpus0")
    digest = bytes.fromhex(digest_hex)
    return {
        "query": [str(x) for x in query],
        "corpus0": [str(x) for x in corpus[0]],
        "corpus1": [str(x) for x in corpus[1]],
        "corpus2": [str(x) for x in corpus[2]],
        "emitted": [str(x) for x in emitted],
        "query_bits": [bits_le(x, 8) for x in query],
        "corpus0_bits": [bits_le(x, 8) for x in corpus[0]],
        "corpus1_bits": [bits_le(x, 8) for x in corpus[1]],
        "corpus2_bits": [bits_le(x, 8) for x in corpus[2]],
        "emitted_bits": [bits_le(x, 8) for x in emitted],
        "eq0_inv": [inv_or_zero(a - d) for a in query for d in corpus[0]],
        "eq1_inv": [inv_or_zero(a - d) for a in query for d in corpus[1]],
        "eq2_inv": [inv_or_zero(a - d) for a in query for d in corpus[2]],
        "ge01_bits": bits_le(scores[0] - scores[1], 16),
        "ge02_bits": bits_le(scores[0] - scores[2], 16),
        "expected_digest_bits": [str((digest[k // 8] >> (7 - (k % 8))) & 1) for k in range(256)],
    }


def run(cmd: list[str], cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, check=False)


def toolchain_receipt() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for tool in ("node", "circom", "snarkjs"):
        path = shutil.which(tool)
        if not path:
            raise RuntimeError(f"missing_{tool}")
        cp = run([path, "--version"], ROOT, 30)
        data[tool] = {"path": path, "version": (cp.stdout + cp.stderr).strip()[:500]}
    ptau = ROOT / PTAU
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    if not ptau.exists() or not circomlib.is_dir():
        raise RuntimeError("missing_ptau_or_circomlib")
    return receipt("toolchain", {
        "toolchain": data,
        "ptau": {"path": PTAU, "sha256": file_sha(ptau)},
        "package_lock_sha256": file_sha(ROOT / "package-lock.json"),
    })


def checked(cmd: list[str], cwd: Path, commands: list[dict[str, Any]], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    cp = run(cmd, cwd, timeout)
    commands.append({"cmd": cmd, "returncode": cp.returncode, "stdout_sha256": sha256_hex(cp.stdout.encode()), "stderr_sha256": sha256_hex(cp.stderr.encode())})
    if cp.returncode != 0:
        raise RuntimeError("command_failed")
    return cp


def prove(circuit_input: dict[str, Any]) -> dict[str, Any]:
    tc = toolchain_receipt()
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    work = BUNDLE_DIR
    (work / "input.json").write_text(json.dumps(circuit_input, sort_keys=True), encoding="utf-8")
    commands: list[dict[str, Any]] = []
    circom = shutil.which("circom")
    snarkjs = shutil.which("snarkjs")
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    ptau = ROOT / PTAU
    checked([circom, str(ROOT / "aion.circom"), "--r1cs", "--wasm", "--sym", "-l", str(circomlib), "-o", str(work)], work, commands)
    checked([snarkjs, "groth16", "setup", "aion.r1cs", str(ptau), "aion_0.zkey"], work, commands)
    checked([snarkjs, "zkey", "contribute", "aion_0.zkey", "aion.zkey", "--name=aion", "-e=aion-local-entropy"], work, commands)
    checked([snarkjs, "zkey", "export", "verificationkey", "aion.zkey", "verification_key.json"], work, commands)
    checked([snarkjs, "groth16", "fullprove", "input.json", "aion_js/aion.wasm", "aion.zkey", "proof.json", "public.json"], work, commands)
    checked([snarkjs, "groth16", "verify", "verification_key.json", "public.json", "proof.json"], work, commands, 300)
    pub = json.loads((work / "public.json").read_text())
    pub[LENS["emitted"]] = "0" if pub[LENS["emitted"]] == "1" else "1"
    (work / "public_bad.json").write_text(json.dumps(pub), encoding="utf-8")
    neg = run([snarkjs, "groth16", "verify", "verification_key.json", "public_bad.json", "proof.json"], work, 300)
    if neg.returncode == 0:
        raise RuntimeError("negative_check_passed")
    (work / "toolchain.receipt.json").write_text(json.dumps(tc, indent=2, sort_keys=True) + "\n")
    art = receipt("proof-artifacts", {
        "circuit_source_sha256": file_sha(ROOT / "aion.circom"),
        "input_sha256": file_sha(work / "input.json"),
        "r1cs_sha256": file_sha(work / "aion.r1cs"),
        "wasm_sha256": file_sha(work / "aion_js" / "aion.wasm"),
        "sym_sha256": file_sha(work / "aion.sym"),
        "zkey0_sha256": file_sha(work / "aion_0.zkey"),
        "zkey_sha256": file_sha(work / "aion.zkey"),
        "verification_key_sha256": file_sha(work / "verification_key.json"),
        "proof_sha256": file_sha(work / "proof.json"),
        "public_sha256": file_sha(work / "public.json"),
        "negative_verify_returncode": neg.returncode,
        "commands": commands,
    }, [tc])
    (work / "proof-artifacts.receipt.json").write_text(json.dumps(art, indent=2, sort_keys=True) + "\n")
    return art


def cycle(query: bytes, corpus: list[bytes]) -> tuple[bytes, str]:
    winner = select_winner(query, corpus)
    emitted = bytes(corpus[winner])
    return emitted, sha256_hex(query + corpus[0] + corpus[1] + corpus[2] + emitted)


def statement(transcript_root: str, proof_root: str, artifact: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": "aion-cycle-statement-v1",
        "cycle_id": "aion.one_prompt_closed_loop.v1",
        "policy": "aion.cycle.v1",
        "expected_transcript_root": EXPECTED_TRANSCRIPT_ROOT,
        "transcript_root": transcript_root,
        "proof_root": proof_root,
        "proof_system": "groth16",
        "circuit_hash": artifact["circuit_source_sha256"],
        "verification_key_hash": artifact["verification_key_sha256"],
        "public_input_hash": artifact["public_sha256"],
        "proof_hash": artifact["proof_sha256"],
    }
    payload["cycle_root"] = sha256_hex(canonical_bytes(payload))
    return payload


def execute() -> None:
    fx = json.loads((ROOT / "fixtures" / "canonical.json").read_text())
    q = fx["query"].encode("utf-8", "strict")
    corpus = [c.encode("utf-8", "strict") for c in fx["corpus"]]
    emitted, root = cycle(q, corpus)
    if root != EXPECTED_TRANSCRIPT_ROOT:
        raise RuntimeError("expected_transcript_root_mismatch")
    _, replay = cycle(q, corpus)
    if replay != root:
        raise RuntimeError("replay_mismatch")
    tq = bytearray(q); tq[0] ^= 1
    _, tamper = cycle(bytes(tq), corpus)
    if tamper == root:
        raise RuntimeError("tamper_not_detected")
    art = prove(build_input(q, corpus, emitted, root))
    st = statement(root, art["receipt_hash"], art)
    (ROOT / "aion.statement.json").write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")


def verify_statement(path: Path) -> None:
    data = json.loads(path.read_text())
    body = dict(data); cycle_root = body.pop("cycle_root", None)
    if sha256_hex(canonical_bytes(body)) != cycle_root:
        raise RuntimeError("cycle_root_mismatch")
    if data.get("transcript_root") != EXPECTED_TRANSCRIPT_ROOT:
        raise RuntimeError("transcript_root_mismatch")
    snarkjs = shutil.which("snarkjs")
    if not snarkjs:
        raise RuntimeError("missing_snarkjs")
    cp = run([snarkjs, "groth16", "verify", "verification_key.json", "public.json", "proof.json"], BUNDLE_DIR, 300)
    if cp.returncode != 0:
        raise RuntimeError("portable_verify_failed")
    art = json.loads((BUNDLE_DIR / "proof-artifacts.receipt.json").read_text())
    if art["receipt_hash"] != data.get("proof_root"):
        raise RuntimeError("proof_root_mismatch")
    if file_sha(BUNDLE_DIR / "verification_key.json") != data.get("verification_key_hash"):
        raise RuntimeError("verification_key_hash_mismatch")
    if file_sha(BUNDLE_DIR / "public.json") != data.get("public_input_hash"):
        raise RuntimeError("public_input_hash_mismatch")
    if file_sha(BUNDLE_DIR / "proof.json") != data.get("proof_hash"):
        raise RuntimeError("proof_hash_mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--verify-statement", type=Path)
    args = parser.parse_args()
    try:
        verify_statement(args.verify_statement) if args.verify_statement else execute()
    except Exception:
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
