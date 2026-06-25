# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "aion_cycle.py").read_text(encoding="utf-8")


def test_no_builtin_hash_call() -> None:
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash"


def test_expected_root_is_not_bootstrapped() -> None:
    assert 'EXPECTED_ROOT = "computed-by-aion-cycle-reference-on-first-release"' in SOURCE
    assert "BOOTSTRAP_EXPECTED_ROOT" not in SOURCE


def test_circuits_exist() -> None:
    assert (ROOT / "aion_closure_root.circom").is_file()
    assert (ROOT / "aion_digest_limb_closure.circom").is_file()
