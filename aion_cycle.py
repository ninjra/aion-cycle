#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
"""AION reference runner.

One laminar path. One Groth16 proof of the entire canonical cycle, including the
in-circuit SHA-256 commitment over the transcript. Prints exactly PASS or FAIL.
Fails closed if the proof toolchain is missing.
"""
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
RUN_DIR = ROOT / ".aion" / "latest"
LENS = {"query": 30, "corpus0": 42, "corpus1": 33, "corpus2": 24, "emitted": 42}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def file_sha(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def receipt(kind: str, payload: dict[str, Any], children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    child_hashes = [c["receipt_hash"] for c in children or []]
    failed = list(payload.get("failed_checks") or [])
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
    # BN254 scalar field prime.
    p = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    v = int(diff) % p
    return "0" if v == 0 else str(pow(v, -1, p))


def select_winner(query: bytes, corpus: list[bytes]) -> int:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    best = max(range(len(scores)), key=lambda i: (scores[i], [-b for b in corpus[i]]))
    if scores[best] != max(scores) or scores.count(max(scores)) != 1:
        raise RuntimeError("ambiguous_or_no_winner")
    return best


def build_input(query: bytes, corpus: list[bytes], emitted: bytes, digest_hex: str) -> dict[str, Any]:
    def byte_list(b: bytes) -> list[str]:
        return [str(x) for x in b]

    def byte_bits(b: bytes) -> list[list[str]]:
        return [bits_le(x, 8) for x in b]

    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c) [k] for k in cq) for c in corpus]
    ge01 = scores[0] - scores[1]
    ge02 = scores[0] - scores[2]
    if ge01 < 0 or ge02 < 0:
        raise RuntimeError("winner_not_corpus0")

    digest = bytes.fromhex(digest_hex)
    digest_bits = [str((digest[k // 8] >> (7 - (k % 8))) & 1) for k in range(256)]

    return {
        "query": byte_list(query),
        "corpus0": byte_list(corpus[0]),
        "corpus1": byte_list(corpus[1]),
        "corpus2": byte_list(corpus[2]),
        "emitted": byte_list(emitted),
        "query_bits": byte_bits(query),
        "corpus0_bits": byte_bits(corpus[0]),
        "corpus1_bits": byte_bits(corpus[1]),
        "corpus2_bits": byte_bits(corpus[2]),
        "emitted_bits": byte_bits(emitted),
        "eq0_inv": [inv_or_zero(a - d) for a in query for d in corpus[0]],
        "eq1_inv": [inv_or_zero(a - d) for a in query for d in corpus[1]],
        "eq2_inv": [inv_or_zero(a - d) for a in query for d in corpus[2]],
        "ge01_bits": bits_le(ge01, 16),
        "ge02_bits": bits_le(ge02, 16),
        "expected_digest_bits": digest_bits,
    }


def _run(cmd: list[str], cwd: Path, *, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, check=False)


def tool_version(path: str) -> str:
    cp = _run([path, "--version"], ROOT, timeout=30)
    return (cp.stdout + cp.stderr).strip()[:500]


def build_toolchain_receipt() -> dict[str, Any]:
    tools = {}
    for name in ("node", "circom", "snarkjs"):
        path = shutil.which(name)
        if not path:
            raise RuntimeError(f"missing_{name}")
        tools[name] = {"path": path, "version": tool_version(path)}
    ptau = ROOT / PTAU
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    if not ptau.exists() or not circomlib.is_dir():
        raise RuntimeError("missing_ptau_or_circomlib")
    payload = {
        "toolchain": tools,
        "ptau": {"path": PTAU, "sha256": file_sha(ptau)},
        "package_lock_sha256": file_sha(ROOT / "package-lock.json") if (ROOT / "package-lock.json").exists() else "",
    }
    return receipt("toolchain", payload)


def prove_and_verify(circuit_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    tool_r = build_toolchain_receipt()
    work = RUN_DIR / "proof"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    circom = shutil.which("circom")
    snarkjs = shutil.which("snarkjs")
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    ptau = ROOT / PTAU
    input_path = work / "input.json"
    input_path.write_text(json.dumps(circuit_input, sort_keys=True), encoding="utf-8")

    commands: list[dict[str, Any]] = []
    def checked(cmd: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
        cp = _run(cmd, work, timeout=timeout)
        commands.append({"cmd": cmd, "returncode": cp.returncode, "stdout_sha256": sha256_hex(cp.stdout.encode()), "stderr_sha256": sha256_hex(cp.stderr.encode())})
        if cp.returncode != 0:
            raise RuntimeError("command_failed")
        return cp

    checked([circom, str(ROOT / "aion.circom"), "--r1cs", "--wasm", "--sym", "-l", str(circomlib), "-o", str(work)])
    r1cs = work / "aion.r1cs"
    wasm = work / "aion_js" / "aion.wasm"
    sym = work / "aion.sym"
    zkey0 = work / "aion_0.zkey"
    zkey = work / "aion.zkey"
    vkey = work / "verification_key.json"
    proof = work / "proof.json"
    public = work / "public.json"
    checked([snarkjs, "groth16", "setup", str(r1cs), str(ptau), str(zkey0)])
    checked([snarkjs, "zkey", "contribute", str(zkey0), str(zkey), "--name=aion", "-e=aion-local-entropy"])
    checked([snarkjs, "zkey", "export", "verificationkey", str(zkey), str(vkey)])
    checked([snarkjs, "groth16", "fullprove", str(input_path), str(wasm), str(zkey), str(proof), str(public)])
    ok = checked([snarkjs, "groth16", "verify", str(vkey), str(public), str(proof)])
    pub = json.loads(public.read_text(encoding="utf-8"))
    # public layout: emitted[42] then expected_digest_bits[256]; flip first digest bit.
    pub[LENS["emitted"]] = "0" if pub[LENS["emitted"]] == "1" else "1"
    bad = work / "public_bad.json"
    bad.write_text(json.dumps(pub), encoding="utf-8")
    neg = _run([snarkjs, "groth16", "verify", str(vkey), str(bad), str(proof)], work, timeout=300)
    if neg.returncode == 0:
        raise RuntimeError("negative_check_passed")

    artifacts = {
        "circuit_source_sha256": file_sha(ROOT / "aion.circom"),
        "input_sha256": file_sha(input_path),
        "r1cs_sha256": file_sha(r1cs),
        "wasm_sha256": file_sha(wasm),
        "sym_sha256": file_sha(sym),
        "zkey0_sha256": file_sha(zkey0),
        "zkey_sha256": file_sha(zkey),
        "verification_key_sha256": file_sha(vkey),
        "proof_sha256": file_sha(proof),
        "public_sha256": file_sha(public),
        "public_bad_sha256": file_sha(bad),
        "verify_stdout_sha256": sha256_hex(ok.stdout.encode()),
        "verify_stderr_sha256": sha256_hex(ok.stderr.encode()),
        "negative_verify_returncode": neg.returncode,
        "negative_verify_stdout_sha256": sha256_hex(neg.stdout.encode()),
        "negative_verify_stderr_sha256": sha256_hex(neg.stderr.encode()),
        "commands": commands,
    }
    artifact_r = receipt("proof-artifacts", artifacts, [tool_r])
    return artifact_r, artifacts


def cycle(query: bytes, corpus: list[bytes]) -> tuple[bytes, str]:
    winner = select_winner(query, corpus)
    emitted = bytes(corpus[winner])
    transcript = query + corpus[0] + corpus[1] + corpus[2] + emitted
    return emitted, sha256_hex(transcript)


def build_statement(transcript_root: str, proof_root: str, artifacts: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": "aion-cycle-statement-v1",
        "cycle_id": "aion.one_prompt_closed_loop.v1",
        "policy": "aion.cycle.v1",
        "expected_transcript_root": EXPECTED_TRANSCRIPT_ROOT,
        "transcript_root": transcript_root,
        "proof_root": proof_root,
        "proof_system": "groth16",
        "circuit_hash": artifacts["circuit_source_sha256"],
        "verification_key_hash": artifacts["verification_key_sha256"],
        "public_input_hash": artifacts["public_sha256"],
        "proof_hash": artifacts["proof_sha256"],
    }
    payload["cycle_root"] = sha256_hex(canonical_bytes(payload))
    return payload


def execute() -> dict[str, Any]:
    if len(EXPECTED_TRANSCRIPT_ROOT) != 64 or any(c not in "0123456789abcdef" for c in EXPECTED_TRANSCRIPT_ROOT):
        raise RuntimeError("expected_transcript_root_not_frozen")
    fx = json.loads((ROOT / "fixtures" / "canonical.json").read_text(encoding="utf-8"))
    query = fx["query"].encode("utf-8", "strict")
    corpus = [c.encode("utf-8", "strict") for c in fx["corpus"]]
    for name, b in (("query", query), ("corpus0", corpus[0]), ("corpus1", corpus[1]), ("corpus2", corpus[2])):
        if len(b) != LENS[name]:
            raise RuntimeError("fixture_length_mismatch")
    emitted, transcript_root = cycle(query, corpus)
    if transcript_root != EXPECTED_TRANSCRIPT_ROOT:
        raise RuntimeError("expected_transcript_root_mismatch")
    _, replay_root = cycle(query, corpus)
    if replay_root != transcript_root:
        raise RuntimeError("replay_mismatch")
    tampered = bytearray(query)
    tampered[0] ^= 1
    _, tamper_root = cycle(bytes(tampered), corpus)
    if tamper_root == transcript_root:
        raise RuntimeError("tamper_not_detected")
    circuit_input = build_input(query, corpus, emitted, transcript_root)
    proof_r, artifacts = prove_and_verify(circuit_input)
    statement = build_statement(transcript_root, proof_r["receipt_hash"], artifacts)
    if statement["transcript_root"] != EXPECTED_TRANSCRIPT_ROOT:
        raise RuntimeError("statement_transcript_mismatch")
    (ROOT / "aion.statement.json").write_text(json.dumps(statement, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return statement


def verify_statement(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    cycle_root = data.get("cycle_root")
    body = dict(data)
    body.pop("cycle_root", None)
    if sha256_hex(canonical_bytes(body)) != cycle_root:
        raise RuntimeError("cycle_root_mismatch")
    if data.get("transcript_root") != EXPECTED_TRANSCRIPT_ROOT:
        raise RuntimeError("transcript_root_mismatch")


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--verify-statement", type=Path)
    args = parser.parse_args()
    try:
        if args.verify_statement:
            verify_statement(args.verify_statement)
        else:
            execute()
    except Exception:  # noqa: BLE001
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
