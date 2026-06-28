# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_failure_fixtures_are_concrete_json() -> None:
    expected = {
        "tie_score.json",
        "duplicate_field_hash.json",
        "changed_query_byte.json",
        "changed_selected_record.json",
        "changed_public_digest.json",
        "changed_receipt_child_hash.json",
        "unicode_distinct_bytes.json",
        "line_ending_change.json",
    }
    files = {path.name for path in (ROOT / "fixtures" / "fail").glob("*.json")}
    assert expected <= files
    for name in expected:
        payload = json.loads((ROOT / "fixtures" / "fail" / name).read_text(encoding="utf-8"))
        assert payload.get("description")
        assert payload.get("expected_reason") or payload.get("expected_boundary")


def test_pass_fixture_is_concrete_json() -> None:
    payload = json.loads((ROOT / "fixtures" / "pass" / "canonical.json").read_text(encoding="utf-8"))
    assert payload["expected_stdout"] == "PASS"
    assert payload["command"] == "make verify"
