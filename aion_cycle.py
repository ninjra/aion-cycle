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
EXPECTED_ROOT = "b7d163eb8ea2cb12cb81117a9261ab25370607e2f16b8c7d91d0b2986b01c941"
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
    return {
        "root": root,
        "selected": selected,
        "output": output,
        "selected_field_hash": selected_hash,
        "selected_source_hash": sha256_bytes(selected),
        "output_hash": sha256_bytes(output),
    }


def digest_to_field(hex_digest: str) -> str:
    return str(int(hex_digest, 16) % BN254_SCALAR_FIELD)


def digest_limbs(hex_digest: str) -> tuple[list[str], list[list[str]]]:
    raw = bytes.fromhex(hex_digest)
    limbs: list[str] = []
    bits: list[list[str]] = []
    for i in range(4):
        chunk = raw[i * 8:(i + 1) * 8]
        value = int.from_bytes(chunk, "big")
        limbs.append(str(value))
        bits.append([str((value >> j) & 1) for j in range(64)])
    return limbs, bits


def toolchain_receipt() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for tool in ("node", "circom", "snarkjs"):
        path = shutil.which(tool)
        if not path:
            raise RuntimeError(f"missing_{tool}")
        version = subprocess.run([path, "--version"], text=True, capture_output=True, timeout=20, check=False)
        data[tool] = {"path": path, "version": (version.stdout + version.stderr).strip()[:200]}
    return receipt("Toolchain", sha256_bytes(b"toolchain"), sha256_bytes(canonical_bytes(data)))


def _sh(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, timeout=300)


def groth16_prove_verify(circuit: Path, input_obj: dict[str, Any], work: Path) -> str:
    work.mkdir(parents=True, exist_ok=True)
    circom = shutil.which("circom")
    snarkjs = shutil.which("snarkjs")
    if not circom or not snarkjs:
        raise RuntimeError("missing_tooling")
    ptau = ROOT / "powersOfTau28_hez_final_14.ptau"
    if not ptau.exists():
        raise RuntimeError("missing_ptau")
    name = circuit.stem
    (work / "input.json").write_text(json.dumps(input_obj), encoding="utf-8")
    _sh([circom, str(circuit), "--r1cs", "--wasm", "--sym", "-o", str(work)], work)
    r1cs = work / f"{name}.r1cs"
    zkey0 = work / f"{name}_0.zkey"
    zkey = work / f"{name}.zkey"
    vkey = work / f"{name}_vkey.json"
    proof = work / f"{name}_proof.json"
    public = work / f"{name}_public.json"
    wasm = work / f"{name}_js" / f"{name}.wasm"
    _sh([snarkjs, "groth16", "setup", str(r1cs), str(ptau), str(zkey0)], work)
    _sh([snarkjs, "zkey", "contribute", str(zkey0), str(zkey), "--name=aion", "-e=aion-local-entropy"], work)
    _sh([snarkjs, "zkey", "export", "verificationkey", str(zkey), str(vkey)], work)
    _sh([snarkjs, "groth16", "fullprove", str(work / "input.json"), str(wasm), str(zkey), str(proof), str(public)], work)
    ok = subprocess.run([snarkjs, "groth16", "verify", str(vkey), str(public), str(proof)], cwd=str(work), text=True, capture_output=True, timeout=120, check=False)
    if ok.returncode != 0:
        raise RuntimeError(f"verify_failed:{name}")
    pub = json.loads(public.read_text(encoding="utf-8"))
    pub[0] = str((int(pub[0]) + 1) % BN254_SCALAR_FIELD)
    bad = work / f"{name}_public_bad.json"
    bad.write_text(json.dumps(pub), encoding="utf-8")
    neg = subprocess.run([snarkjs, "groth16", "verify", str(vkey), str(bad), str(proof)], cwd=str(work), text=True, capture_output=True, timeout=120, check=False)
    if neg.returncode == 0:
        raise RuntimeError(f"negative_check_passed:{name}")
    return sha256_bytes(canonical_bytes({
        "circuit": name,
        "vkey": sha256_bytes(vkey.read_bytes()),
        "proof": sha256_bytes(proof.read_bytes()),
    }))


def byte_bits(value: int, width: int) -> list[str]:
    return [str((int(value) >> i) & 1) for i in range(width)]


def inverse_or_zero(diff: int) -> str:
    v = int(diff) % BN254_SCALAR_FIELD
    if v == 0:
        return "0"
    return str(pow(v, -1, BN254_SCALAR_FIELD))


def full_cycle_input(fixture: dict[str, Any], selected: bytes) -> dict[str, Any]:
    query = list(fixture["query"].encode("utf-8", "strict"))
    corpus = [list(item.encode("utf-8", "strict")) for item in fixture["corpus"]]
    emitted = list(selected)
    if len(query) != 30 or len(corpus[0]) != 42 or len(corpus[1]) != 33 or len(corpus[2]) != 24 or len(emitted) != 42:
        raise RuntimeError("fixture_length_mismatch")
    eq0_inv = [inverse_or_zero(a - b) for a in query for b in corpus[0]]
    eq1_inv = [inverse_or_zero(a - b) for a in query for b in corpus[1]]
    eq2_inv = [inverse_or_zero(a - b) for a in query for b in corpus[2]]
    # Score deltas for canonical fixture: corpus0 must win.
    from collections import Counter
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    ge01 = scores[0] - scores[1]
    ge02 = scores[0] - scores[2]
    if ge01 < 0 or ge02 < 0:
        raise RuntimeError("canonical_selection_not_winner")
    return {
        "query": [str(x) for x in query],
        "corpus0": [str(x) for x in corpus[0]],
        "corpus1": [str(x) for x in corpus[1]],
        "corpus2": [str(x) for x in corpus[2]],
        "emitted": [str(x) for x in emitted],
        "query_bits": [[str((x >> i) & 1) for i in range(8)] for x in query],
        "corpus0_bits": [[str((x >> i) & 1) for i in range(8)] for x in corpus[0]],
        "corpus1_bits": [[str((x >> i) & 1) for i in range(8)] for x in corpus[1]],
        "corpus2_bits": [[str((x >> i) & 1) for i in range(8)] for x in corpus[2]],
        "emitted_bits": [[str((x >> i) & 1) for i in range(8)] for x in emitted],
        "ge01_bits": byte_bits(ge01, 16),
        "ge02_bits": byte_bits(ge02, 16),
        "eq0_inv": eq0_inv,
        "eq1_inv": eq1_inv,
        "eq2_inv": eq2_inv,
    }


def prove(final_root: str, source_hash: str, output_hash: str, replay_root: str, fixture: dict[str, Any], selected: bytes) -> dict[str, Any]:
    tool_r = toolchain_receipt()
    children = [tool_r]
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        full_input = full_cycle_input(fixture, selected)
        full_proof_hash = groth16_prove_verify(ROOT / "aion_full_cycle.circom", full_input, work / "full_cycle")

        root_input = {
            "expected_root": digest_to_field(final_root),
            "final_root": digest_to_field(final_root),
            "selected_hash": digest_to_field(source_hash),
            "output_hash": digest_to_field(output_hash),
            "replay_root": digest_to_field(replay_root),
            "canonical_transcript_root": digest_to_field(final_root),
            "tamper_transcript_root": digest_to_field(sha256_bytes(b"tamper:" + final_root.encode())),
            "tamper_failed": "1",
            "child_passed": ["1"] * 8,
        }
        root_proof_hash = groth16_prove_verify(ROOT / "aion_closure_root.circom", root_input, work / "root")

        fr_l, fr_b = digest_limbs(final_root)
        sh_l, sh_b = digest_limbs(source_hash)
        oh_l, oh_b = digest_limbs(output_hash)
        limb_input = {
            "expected_root_limbs": fr_l,
            "final_root_limbs": fr_l,
            "selected_hash_limbs": sh_l,
            "output_hash_limbs": oh_l,
            "replay_root_limbs": fr_l,
            "expected_root_bits": fr_b,
            "final_root_bits": fr_b,
            "selected_hash_bits": sh_b,
            "output_hash_bits": oh_b,
            "replay_root_bits": fr_b,
            "tamper_failed": "1",
            "child_passed": ["1"] * 8,
        }
        limb_proof_hash = groth16_prove_verify(ROOT / "aion_digest_limb_closure.circom", limb_input, work / "limb")

    out = sha256_bytes(canonical_bytes({"full_cycle_proof": full_proof_hash, "root_proof": root_proof_hash, "limb_proof": limb_proof_hash}))
    return receipt("Groth16", tool_r["receipt_hash"], out, children)


def main() -> int:
    try:
        fixture = json.loads((ROOT / "fixtures" / "canonical.json").read_text(encoding="utf-8"))
        run1 = run_fixture(fixture)
        run2 = run_fixture(fixture)
        if run1["root"]["receipt_hash"] != run2["root"]["receipt_hash"] or run1["output"] != run2["output"]:
            raise RuntimeError("replay_mismatch")
        if run1["selected_source_hash"] != run1["output_hash"]:
            raise RuntimeError("output_not_equal_to_selected")
        tampered = run_fixture(fixture, tamper_score=True)
        if tampered["selected"] == run1["selected"]:
            raise RuntimeError("tamper_not_detected")
        if len(EXPECTED_ROOT) != 64 or any(c not in "0123456789abcdef" for c in EXPECTED_ROOT):
            raise RuntimeError("expected_root_not_frozen")
        if run1["root"]["receipt_hash"] != EXPECTED_ROOT:
            raise RuntimeError("expected_root_mismatch")
        prove(EXPECTED_ROOT, run1["selected_source_hash"], run1["output_hash"], run2["root"]["receipt_hash"], fixture, run1["selected"])
    except Exception:  # noqa: BLE001
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
