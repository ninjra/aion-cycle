# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

from pathlib import Path
import ast
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "aion_cycle.py").read_text(encoding="utf-8")
EXPECTED = (ROOT / "expected_root.txt").read_text(encoding="utf-8").strip()


def _run_verify() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "aion_cycle.py", "--verify-statement", "aion.statement.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def _assert_verify_fails() -> None:
    result = _run_verify()
    assert result.stdout.strip() == "FAIL"
    assert result.returncode == 1


def test_no_builtin_hash_call() -> None:
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash"


def test_expected_transcript_root_is_frozen() -> None:
    assert len(EXPECTED) == 64 and all(c in "0123456789abcdef" for c in EXPECTED)
    assert f'EXPECTED_TRANSCRIPT_ROOT = "{EXPECTED}"' in SOURCE
    assert "computed-by-" not in SOURCE


def test_single_full_cycle_circuit_present() -> None:
    circuit = (ROOT / "aion.circom").read_text(encoding="utf-8")
    assert "Sha256(1480)" in circuit
    assert "corpus0" in circuit and "emitted" in circuit
    assert "component main" in circuit


def test_statement_portable_verifies() -> None:
    result = _run_verify()
    assert result.stdout.strip() == "PASS"
    assert result.returncode == 0


def test_statement_cycle_root_mutation_fails(tmp_path: Path) -> None:
    path = ROOT / "aion.statement.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data["cycle_root"] = "0" * 64
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_statement_proof_hash_mutation_fails() -> None:
    path = ROOT / "aion.statement.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data["proof_hash"] = "0" * 64
    body = dict(data)
    body.pop("cycle_root", None)
    # Even if an attacker recomputes the envelope root, artifact hash verification must fail.
    import hashlib
    data["cycle_root"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_public_input_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "public.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data[0] = "0" if data[0] != "0" else "1"
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_artifact_receipt_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "proof-artifacts.receipt.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data["proof_hash"] = "0" * 64
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_toolchain_receipt_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "toolchain.receipt.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data["toolchain"]["node"]["version"] = "tampered"
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_public_digest_bit_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "public.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    idx = 42  # first public digest bit after emitted bytes
    data[idx] = "0" if data[idx] != "0" else "1"
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_public_receipts_do_not_leak_local_absolute_paths() -> None:
    for rel in ("aion.statement.json", "proofs/v1/toolchain.receipt.json", "proofs/v1/proof-artifacts.receipt.json"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "/home/" not in text
        assert "/usr/bin" not in text


def test_generation_trace_receipt_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "generation-trace.receipt.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    data["commands"][0]["returncode"] = 99
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails()
    finally:
        path.write_text(original, encoding="utf-8")


def test_stored_public_bad_is_not_trusted() -> None:
    path = ROOT / "proofs" / "v1" / "public_bad.json"
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    # Make the stored public_bad equal to public.json. Verifier must ignore it and
    # regenerate public_bad_reverify.json from public.json, so verification still passes.
    data = json.loads((ROOT / "proofs" / "v1" / "public.json").read_text(encoding="utf-8"))
    try:
        path.write_text(json.dumps(data), encoding="utf-8")
        result = _run_verify()
        assert result.stdout.strip() == "PASS"
        assert result.returncode == 0
    finally:
        path.write_text(original, encoding="utf-8")


def test_missing_snarkjs_fails(monkeypatch) -> None:
    import aion_cycle
    original = aion_cycle.shutil.which
    def fake_which(name: str):
        if name == "snarkjs":
            return None
        return original(name)
    monkeypatch.setattr(aion_cycle.shutil, "which", fake_which)
    try:
        aion_cycle.verify_statement(ROOT / "aion.statement.json")
    except RuntimeError as exc:
        assert "missing_snarkjs" in str(exc)
    else:
        raise AssertionError("missing snarkjs did not fail")


def test_missing_circom_fails(monkeypatch) -> None:
    import aion_cycle
    original = aion_cycle.shutil.which
    def fake_which(name: str):
        if name == "circom":
            return None
        return original(name)
    monkeypatch.setattr(aion_cycle.shutil, "which", fake_which)
    try:
        aion_cycle.execute()
    except RuntimeError as exc:
        assert "missing_circom" in str(exc)
    else:
        raise AssertionError("missing circom did not fail")
