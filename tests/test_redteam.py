# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "aion_cycle.py").read_text(encoding="utf-8")
EXPECTED = (ROOT / "expected_root.txt").read_text(encoding="utf-8").strip()


def test_no_builtin_hash_call() -> None:
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "hash"


def test_expected_root_is_frozen() -> None:
    assert len(EXPECTED) == 64 and all(c in "0123456789abcdef" for c in EXPECTED)
    assert f'EXPECTED_ROOT = "{EXPECTED}"' in SOURCE
    assert "computed-by-" not in SOURCE


def test_single_circuit_present() -> None:
    assert (ROOT / "aion.circom").is_file()
