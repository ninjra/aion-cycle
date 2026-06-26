#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
"""AION reference runner.

One laminar path. One Groth16 proof of the entire canonical cycle, including the
in-circuit SHA-256 commitment over the transcript. Prints exactly PASS or FAIL.
Fails closed if the proof toolchain is missing.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

BN254_SCALAR_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617
EXPECTED_ROOT = "4fe55b20021791ebb3ca62b2773ea689e59deab6f68c3ecdea36ae37ab3a47a7"
PTAU = "powersOfTau28_hez_final_17.ptau"
ROOT = Path(__file__).resolve().parent
LENS = {"query": 30, "corpus0": 42, "corpus1": 33, "corpus2": 24, "emitted": 42}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bits_le(value: int, width: int) -> list[str]:
    return [str((int(value) >> i) & 1) for i in range(width)]


def inv_or_zero(diff: int) -> str:
    v = int(diff) % BN254_SCALAR_FIELD
    return "0" if v == 0 else str(pow(v, -1, BN254_SCALAR_FIELD))


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

    eq_inv = []
    for cn, c in (("0", corpus[0]), ("1", corpus[1]), ("2", corpus[2])):
        eq_inv.append([inv_or_zero(a - d) for a in query for d in c])

    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    ge01 = scores[0] - scores[1]
    ge02 = scores[0] - scores[2]
    if ge01 < 0 or ge02 < 0:
        raise RuntimeError("winner_not_corpus0")

    digest = bytes.fromhex(digest_hex)
    digest_bits = []
    for k in range(256):
        byte = digest[k // 8]
        digest_bits.append(str((byte >> (7 - (k % 8))) & 1))

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
        "eq0_inv": eq_inv[0],
        "eq1_inv": eq_inv[1],
        "eq2_inv": eq_inv[2],
        "ge01_bits": bits_le(ge01, 16),
        "ge02_bits": bits_le(ge02, 16),
        "expected_digest_bits": digest_bits,
    }


def _sh(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, timeout=900)


def prove_and_verify(circuit_input: dict[str, Any]) -> None:
    circom = shutil.which("circom")
    snarkjs = shutil.which("snarkjs")
    if not circom or not snarkjs:
        raise RuntimeError("missing_tooling")
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    ptau = ROOT / PTAU
    if not circomlib.is_dir() or not ptau.exists():
        raise RuntimeError("missing_circomlib_or_ptau")
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / "input.json").write_text(json.dumps(circuit_input), encoding="utf-8")
        _sh([circom, str(ROOT / "aion.circom"), "--r1cs", "--wasm", "--sym", "-l", str(circomlib), "-o", str(work)], work)
        r1cs = work / "aion.r1cs"
        wasm = work / "aion_js" / "aion.wasm"
        zkey0 = work / "aion_0.zkey"
        zkey = work / "aion.zkey"
        vkey = work / "vkey.json"
        proof = work / "proof.json"
        public = work / "public.json"
        _sh([snarkjs, "groth16", "setup", str(r1cs), str(ptau), str(zkey0)], work)
        _sh([snarkjs, "zkey", "contribute", str(zkey0), str(zkey), "--name=aion", "-e=aion-local-entropy"], work)
        _sh([snarkjs, "zkey", "export", "verificationkey", str(zkey), str(vkey)], work)
        _sh([snarkjs, "groth16", "fullprove", str(work / "input.json"), str(wasm), str(zkey), str(proof), str(public)], work)
        ok = subprocess.run([snarkjs, "groth16", "verify", str(vkey), str(public), str(proof)], cwd=str(work), text=True, capture_output=True, timeout=300, check=False)
        if ok.returncode != 0:
            raise RuntimeError("verify_failed")
        pub = json.loads(public.read_text(encoding="utf-8"))
        # public layout: emitted[42] then expected_digest_bits[256]; flip first digest bit.
        i = LENS["emitted"]
        pub[i] = "0" if pub[i] == "1" else "1"
        bad = work / "public_bad.json"
        bad.write_text(json.dumps(pub), encoding="utf-8")
        neg = subprocess.run([snarkjs, "groth16", "verify", str(vkey), str(bad), str(proof)], cwd=str(work), text=True, capture_output=True, timeout=300, check=False)
        if neg.returncode == 0:
            raise RuntimeError("negative_check_passed")


def cycle(query: bytes, corpus: list[bytes]) -> tuple[bytes, str]:
    winner = select_winner(query, corpus)
    selected = corpus[winner]
    emitted = bytes(selected)
    if emitted != selected:
        raise RuntimeError("output_not_exact")
    transcript = query + corpus[0] + corpus[1] + corpus[2] + emitted
    return emitted, sha256_hex(transcript)


def main() -> int:
    try:
        if len(EXPECTED_ROOT) != 64 or any(c not in "0123456789abcdef" for c in EXPECTED_ROOT):
            raise RuntimeError("expected_root_not_frozen")
        fx = json.loads((ROOT / "fixtures" / "canonical.json").read_text(encoding="utf-8"))
        query = fx["query"].encode("utf-8", "strict")
        corpus = [c.encode("utf-8", "strict") for c in fx["corpus"]]
        for name, b in (("query", query), ("corpus0", corpus[0]), ("corpus1", corpus[1]), ("corpus2", corpus[2])):
            if len(b) != LENS[name]:
                raise RuntimeError("fixture_length_mismatch")

        emitted, digest = cycle(query, corpus)
        if len(emitted) != LENS["emitted"]:
            raise RuntimeError("emitted_length_mismatch")
        # replay must match
        _, digest2 = cycle(query, corpus)
        if digest != digest2:
            raise RuntimeError("replay_mismatch")
        # tamper must change the commitment
        tampered_query = bytearray(query)
        tampered_query[0] ^= 0x01
        _, tdigest = cycle(bytes(tampered_query), corpus)
        if tdigest == digest:
            raise RuntimeError("tamper_not_detected")
        if digest != EXPECTED_ROOT:
            raise RuntimeError("expected_root_mismatch")
        if corpus[0] != emitted:
            raise RuntimeError("winner_not_emitted")

        circuit_input = build_input(query, corpus, emitted, digest)
        prove_and_verify(circuit_input)
    except Exception:  # noqa: BLE001
        print("FAIL")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
