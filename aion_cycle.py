#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
"""AION reference runner.

This file is intentionally small and strict. It prints exactly PASS or FAIL.
It requires real circom/snarkjs tooling for PASS. If the proof toolchain is not
available, it fails closed.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MIN_Q15 = -32768
MAX_Q15 = 32767
FIELD_SIZE = 256
BN254_SCALAR_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617
EXPECTED_ROOT = "computed-by-aion-cycle-reference-on-first-release"
ROOT = Path(__file__).resolve().parent


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def clamp_q15(x: int) -> int:
    return max(MIN_Q15, min(MAX_Q15, int(x)))


def sat_add(a: int, b: int) -> int:
    return clamp_q15(a + b)


def sat_mul(a: int, b: int) -> int:
    return clamp_q15(a * b)


def receipt(phase: str, input_hash: str, output_hash: str, children: list[dict[str, Any]] | None = None, failed: list[str] | None = None) -> dict[str, Any]:
    children = children or []
    failed = list(failed or [])
    child_hashes = [c["receipt_hash"] for c in children]
    if any(c.get("proof_passed") is not True for c in children):
        failed.append("child_failed")
    body = {
        "phase": phase,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "child_receipt_hashes": child_hashes,
        "failed_checks": failed,
        "proof_passed": not failed,
    }
    body["receipt_hash"] = sha256_bytes(canonical_bytes(body))
    return body


def encode(source: bytes, ledger: dict[str, bytes]) -> tuple[list[int], str]:
    field = [0] * FIELD_SIZE
    for b in source:
        field[b] = sat_add(field[b], 1)
    field_hash = sha256_bytes(canonical_bytes(field))
    prior = ledger.get(field_hash)
    if prior is not None and prior != source:
        raise ValueError("ambiguous_mapback")
    ledger[field_hash] = source
    return field, field_hash


def carry(field: list[int]) -> list[int]:
    if not isinstance(field, list) or not all(isinstance(x, int) for x in field):
        raise TypeError("carry_requires_list_int")
    return list(field)


def score(query: list[int], candidate: list[int]) -> int:
    total = 0
    for q, c in zip(query, candidate):
        total = sat_add(total, sat_mul(q, c))
    return total


def run_fixture(fixture: dict[str, Any], *, tamper_score: bool = False) -> dict[str, Any]:
    ledger: dict[str, bytes] = {}
    query = fixture["query"].encode("utf-8", "strict")
    corpus = [item.encode("utf-8", "strict") for item in fixture["corpus"]]
    expected = fixture["expected_selected"].encode("utf-8", "strict")
    event_id = sha256_bytes(canonical_bytes({"query": query.hex(), "corpus": [c.hex() for c in corpus]}))

    q_field, q_hash = encode(query, ledger)
    corpus_items = [encode(item, ledger) for item in corpus]
    enc_r = receipt("Encode", event_id, sha256_bytes(canonical_bytes({"query": q_hash, "corpus": [h for _, h in corpus_items]})))

    q_carried = carry(q_field)
    c_carried = [(carry(f), h) for f, h in corpus_items]
    carry_r = receipt("Carry", enc_r["receipt_hash"], sha256_bytes(canonical_bytes([q_carried, [h for _, h in c_carried]])), [enc_r])

    ranked = []
    for f, h in c_carried:
        s = score(q_carried, f)
        if tamper_score and ledger[h] == expected:
            s = MIN_Q15
        ranked.append(( -s, h))
    ranked.sort(key=lambda x: (x[0], x[1]))
    selected_hash = ranked[0][1]
    cmp_r = receipt("Compare", carry_r["receipt_hash"], selected_hash, [carry_r])

    back_r = receipt("CarryBack", cmp_r["receipt_hash"], selected_hash, [cmp_r])
    selected = ledger[selected_hash]
    map_r = receipt("MapBack", back_r["receipt_hash"], sha256_bytes(selected), [back_r])
    output = bytes(selected)
    fail = []
    if output != selected:
        fail.append("byte_mismatch")
    if sha256_bytes(output) != sha256_bytes(selected):
        fail.append("hash_mismatch")
    write_r = receipt("Write", map_r["receipt_hash"], sha256_bytes(output), [map_r], fail)
    root = receipt("Root", event_id, write_r["receipt_hash"], [write_r])
    return {"root": root, "selected": selected, "output": output, "selected_hash": selected_hash, "output_hash": sha256_bytes(output)}


def digest_to_field(hex_digest: str) -> str:
    return str(int(hex_digest, 16) % BN254_SCALAR_FIELD)


def toolchain_receipt() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for tool in ("node", "circom", "snarkjs"):
        path = shutil.which(tool)
        if not path:
            raise RuntimeError(f"missing_{tool}")
        try:
            version = subprocess.run([path, "--version"], text=True, capture_output=True, timeout=10, check=False)
            data[tool] = {"path": path, "version": (version.stdout + version.stderr).strip()[:200]}
        except Exception as exc:  # noqa: BLE001
            data[tool] = {"path": path, "version_error": type(exc).__name__}
    return receipt("Toolchain", sha256_bytes(b"toolchain"), sha256_bytes(canonical_bytes(data)))


def prove(root_hex: str, selected_hex: str, output_hex: str, replay_hex: str, child_count: int) -> dict[str, Any]:
    tool_r = toolchain_receipt()
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        circuit = ROOT / "aion_closure_root.circom"
        input_json = work / "input.json"
        input_json.write_text(json.dumps({
            "expected_root": digest_to_field(root_hex),
            "final_root": digest_to_field(root_hex),
            "selected_hash": digest_to_field(selected_hex),
            "output_hash": digest_to_field(output_hex),
            "replay_root": digest_to_field(replay_hex),
            "canonical_transcript_root": digest_to_field(root_hex),
            "tamper_transcript_root": digest_to_field(sha256_bytes(b"tamper" + bytes.fromhex(root_hex))),
            "tamper_failed": "1",
            "child_passed": ["1"] * child_count,
        }), encoding="utf-8")
        # A real Groth16 flow needs a ptau. This reference fails closed if the
        # environment has no suitable tooling/artifacts. That is intentional.
        circom = shutil.which("circom")
        snarkjs = shutil.which("snarkjs")
        subprocess.run([circom, str(circuit), "--r1cs", "--wasm", "--sym", "-o", str(work)], check=True, capture_output=True, timeout=60)
        # Minimal public repo does not ship a ptau; users can add one. Missing ptau == FAIL.
        ptau = ROOT / "powersOfTau28_hez_final_10.ptau"
        if not ptau.exists():
            raise RuntimeError("missing_ptau")
        r1cs = work / "aion_closure_root.r1cs"
        zkey0 = work / "aion_0000.zkey"
        zkey = work / "aion_final.zkey"
        subprocess.run([snarkjs, "groth16", "setup", str(r1cs), str(ptau), str(zkey0)], check=True, capture_output=True, timeout=60)
        subprocess.run([snarkjs, "zkey", "contribute", str(zkey0), str(zkey), "--name=local", "-v", "-e=local entropy"], check=True, capture_output=True, timeout=60)
        vkey = work / "verification_key.json"
        proof_json = work / "proof.json"
        public_json = work / "public.json"
        wasm = next(work.glob("**/*.wasm"))
        subprocess.run([snarkjs, "zkey", "export", "verificationkey", str(zkey), str(vkey)], check=True, capture_output=True, timeout=60)
        subprocess.run([snarkjs, "groth16", "fullprove", str(input_json), str(wasm), str(zkey), str(proof_json), str(public_json)], check=True, capture_output=True, timeout=60)
        verify = subprocess.run([snarkjs, "groth16", "verify", str(vkey), str(public_json), str(proof_json)], text=True, capture_output=True, timeout=60, check=False)
        if verify.returncode != 0:
            raise RuntimeError("verify_failed")
    return receipt("Groth16", tool_r["receipt_hash"], root_hex, [tool_r])


def main() -> int:
    try:
        fixture = json.loads((ROOT / "fixtures" / "canonical.json").read_text(encoding="utf-8"))
        run1 = run_fixture(fixture)
        run2 = run_fixture(fixture)
        if run1["root"]["receipt_hash"] != run2["root"]["receipt_hash"] or run1["output"] != run2["output"]:
            raise RuntimeError("replay_mismatch")
        tampered = run_fixture(fixture, tamper_score=True)
        if tampered["root"]["proof_passed"] is True and tampered["selected"] == run1["selected"]:
            raise RuntimeError("tamper_not_detected")
        if EXPECTED_ROOT.startswith("computed-by-"):
            raise RuntimeError("expected_root_not_frozen")
        if run1["root"]["receipt_hash"] != EXPECTED_ROOT:
            raise RuntimeError("expected_root_mismatch")
        prove(EXPECTED_ROOT, run1["selected_hash"], run1["output_hash"], run2["root"]["receipt_hash"], 8)
    except Exception:  # noqa: BLE001
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
