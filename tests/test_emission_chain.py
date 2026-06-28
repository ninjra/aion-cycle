# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

import aion_cycle

ROOT = Path(__file__).resolve().parents[1]
EMISSIONS = ROOT / "proofs" / "v1" / "emissions"


def _run_verify() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "aion_cycle.py", "--verify-statement", "aion.statement.json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )


def _assert_verify_fails(reason: str) -> None:
    result = _run_verify()
    assert result.stdout.strip() == "FAIL"
    assert result.returncode == 1
    assert f"FAIL_REASON:{reason}" in result.stderr


def _mutate(path: Path, mutator, reason: str) -> None:
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)
    mutator(data)
    try:
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _assert_verify_fails(reason)
    finally:
        path.write_text(original, encoding="utf-8")


def test_emission_chain_canonical_verifies() -> None:
    result = _run_verify()
    assert result.stdout.strip() == "PASS"
    assert result.returncode == 0


def test_transition_emissions_present_and_ordered() -> None:
    transitions, final = aion_cycle.load_emission_chain()
    assert [item["transition_id"] for item in transitions] == [spec[1] for spec in aion_cycle.TRANSITION_SPECS]
    assert final["transition_emission_hashes"] == [item["claimed_emission_hash"] for item in transitions]




def test_phase_receipts_present_and_ordered() -> None:
    receipts = aion_cycle.load_phase_receipts()
    assert [r["phase"] for r in receipts] == aion_cycle.PHASE_RECEIPT_ORDER
    assert receipts[-1]["phase_receipt_hashes"] == [r["receipt_hash"] for r in receipts[:-1]]


def test_phase_receipt_mutation_fails() -> None:
    path = ROOT / "proofs" / "v1" / "receipts" / "03-compare.receipt.json"
    _mutate(path, lambda data: data["output_identity"].__setitem__("sha256", "0" * 64), "receipt_hash_mismatch")


def test_missing_source_root_fails() -> None:
    path = EMISSIONS / "01-encode.emission.json"
    _mutate(path, lambda data: data.pop("source_root", None), "emission_1_source_root_mismatch")


def test_wrong_source_root_fails() -> None:
    path = EMISSIONS / "01-encode.emission.json"
    _mutate(path, lambda data: data.__setitem__("source_root", {"label": "bad", "sha256": "0" * 64, "byte_count": 1}), "emission_1_source_root_mismatch")


def test_wrong_previous_emission_hash_fails() -> None:
    path = EMISSIONS / "02-carry.emission.json"
    _mutate(path, lambda data: data.__setitem__("previous_emission_hash", "0" * 64), "emission_2_previous_emission_hash_mismatch")


def test_reordered_transition_index_fails() -> None:
    path = EMISSIONS / "03-compare.emission.json"
    _mutate(path, lambda data: data.__setitem__("transition_index", 4), "emission_3_transition_index_mismatch")


def test_claimed_pass_on_broken_emission_fails() -> None:
    path = EMISSIONS / "04-carry-back.emission.json"
    def change(data):
        data["output_identity"]["sha256"] = "0" * 64
        data["claimed_passed"] = True
    _mutate(path, change, "emission_4_output_identity_mismatch")


def test_removed_child_from_final_emission_fails() -> None:
    path = EMISSIONS / "final-cycle.emission.json"
    _mutate(path, lambda data: data.__setitem__("transition_emission_hashes", data["transition_emission_hashes"][:-1]), "final_emission_transition_emission_hashes_mismatch")


def test_final_chain_tip_mutation_fails() -> None:
    path = EMISSIONS / "final-cycle.emission.json"
    _mutate(path, lambda data: data.__setitem__("chain_tip", "0" * 64), "final_emission_chain_tip_mismatch")


def test_orphan_section_reentry_fails() -> None:
    transitions, final = aion_cycle.load_emission_chain()
    section = dict(transitions[2])
    section["claimed_emission_hash"] = "0" * 64
    data = json.loads((ROOT / "aion.statement.json").read_text(encoding="utf-8"))
    with pytest.raises(RuntimeError, match="section_not_in_final_emission"):
        aion_cycle.verify_section_reentry(data, section, transitions, final)


def test_every_section_can_reenter_verification() -> None:
    transitions, final = aion_cycle.load_emission_chain()
    data = json.loads((ROOT / "aion.statement.json").read_text(encoding="utf-8"))
    for section in transitions:
        aion_cycle.verify_section_reentry(data, section, transitions, final)


def test_cache_valid_flag_ignored_when_bytes_hash_mismatch() -> None:
    cache = {"cache_valid": True, "material_hex": b"wrong".hex()}
    with pytest.raises(RuntimeError, match="cache_material_hash_mismatch"):
        aion_cycle.verify_cache_material(cache, "0" * 64)


def test_cache_material_accepts_recomputed_hash_only() -> None:
    data = b"material"
    cache = {"cache_valid": False, "material_hex": data.hex()}
    assert aion_cycle.verify_cache_material(cache, aion_cycle.sha256_hex(data)) is True
