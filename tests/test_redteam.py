# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from pathlib import Path
import ast
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "aion_cycle.py").read_text(encoding="utf-8")
EXPECTED = (ROOT / "expected_root.txt").read_text(encoding="utf-8").strip()


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
    assert "Sha256(1368)" in circuit
    assert "corpus0" in circuit and "emitted" in circuit
    assert "component main" in circuit


def test_statement_has_three_roots_and_bundle_hashes() -> None:
    st = json.loads((ROOT / "aion.statement.json").read_text(encoding="utf-8"))
    assert st["transcript_root"] == EXPECTED
    assert len(st["proof_root"]) == 64
    assert len(st["cycle_root"]) == 64
    for name in ("proof.json", "public.json", "verification_key.json", "proof-artifacts.receipt.json", "toolchain.receipt.json"):
        assert (ROOT / "proofs" / "v1" / name).is_file()


def test_statement_portable_verifies_if_toolchain_available() -> None:
    result = subprocess.run(
        [sys.executable, "aion_cycle.py", "--verify-statement", "aion.statement.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.stdout.strip() == "PASS"
    assert result.returncode == 0
