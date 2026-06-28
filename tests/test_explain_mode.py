# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "aion_cycle.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )


def test_plain_verify_stdout_is_exactly_pass() -> None:
    result = _run(["--verify-statement", "aion.statement.json"])
    assert result.returncode == 0
    assert result.stdout == "PASS\n"


def test_verify_explain_lists_checks_on_pass() -> None:
    result = _run(["--verify-statement", "aion.statement.json", "--explain"])
    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert lines[0] == "PASS"
    assert any(line.startswith("checked: ") for line in lines[1:])
    # Plain stdout contract is preserved: PASS first, diagnostics are additive.


def test_verify_explain_emits_reason_and_next_on_fail() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "aion.statement.json"
        data = json.loads((ROOT / "aion.statement.json").read_text(encoding="utf-8"))
        data["proof_hash"] = "0" * 64
        bad.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = _run(["--verify-statement", str(bad), "--explain"])
    assert result.returncode == 1
    assert result.stdout == "FAIL\n"
    assert "FAIL_REASON:" in result.stderr
    assert "next:" in result.stderr
