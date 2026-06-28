# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIRCUIT = (ROOT / "aion.circom").read_text(encoding="utf-8")


def test_input_signal_sizes_present() -> None:
    for decl in (
        "signal input query[30];",
        "signal input corpus0[42];",
        "signal input corpus1[33];",
        "signal input corpus2[24];",
        "signal input emitted[42];",
        "signal input expected_digest_bits[256];",
        "signal input ge01_bits[16];",
        "signal input ge02_bits[16];",
    ):
        assert decl in CIRCUIT, decl


def test_public_signals_declared() -> None:
    assert "component main { public [emitted, expected_digest_bits] } = AionCycle();" in CIRCUIT


def test_winner_output_binding_present() -> None:
    for i in range(42):
        assert f"emitted[{i}] === corpus0[{i}];" in CIRCUIT


def test_digest_equality_binding_present() -> None:
    for i in range(256):
        assert f"sha.out[{i}] === expected_digest_bits[{i}];" in CIRCUIT


def test_score_comparison_is_range_bound() -> None:
    # The comparison must bind ge0x to a 16-bit decomposition, else it is vacuous.
    assert re.search(r"ge01 === ge01_bits\[0\] \* 1 \+", CIRCUIT)
    assert re.search(r"ge02 === ge02_bits\[0\] \* 1 \+", CIRCUIT)
    assert "ge01_bits[15] * 32768;" in CIRCUIT
    assert "ge02_bits[15] * 32768;" in CIRCUIT
    assert "ge01_bits[0] * (ge01_bits[0] - 1) === 0;" in CIRCUIT
    assert "ge02_bits[0] * (ge02_bits[0] - 1) === 0;" in CIRCUIT


def test_equality_gadget_present() -> None:
    assert "eq0[0] <== 1 - (query[0] - corpus0[0]) * eq0_inv[0];" in CIRCUIT
    assert "(query[0] - corpus0[0]) * eq0[0] === 0;" in CIRCUIT
    assert "eq0[0] * (eq0[0] - 1) === 0;" in CIRCUIT


def test_sha256_transcript_width() -> None:
    assert "component sha = Sha256(1480);" in CIRCUIT
