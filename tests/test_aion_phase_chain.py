# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial

import aion_cycle


def test_aion_cycle_groth16_phase_chain_theorem_binds_one_repeated_cycle() -> None:
    chain = aion_cycle.aion_initial_chain_hash(b"role: corpus\ncontent-length: 4\n\ndata")
    for phase_index, phase_id in enumerate(aion_cycle.AION_LAMINAR_ROUTE):
        receipt = aion_cycle.aion_phase_chain_theorem_receipt(
            phase_id=phase_id,
            phase_index=phase_index,
            input_chain_hash=chain,
            phase_input=phase_id.encode(),
            phase_output=(phase_id + ":out").encode(),
        )
        assert receipt["proof_passed"] is True
        assert receipt["groth16_scope"] == "one_aion_cycle_repeated_application"
        assert aion_cycle.verify_aion_phase_chain_link(
            receipt, expected_input_chain_hash=chain
        )["proof_passed"] is True
        chain = receipt["output_chain_hash"]


def test_aion_cycle_groth16_phase_chain_theorem_rejects_public_entrypoint_drift() -> None:
    receipt = aion_cycle.aion_phase_chain_theorem_receipt(
        phase_id="energizer",
        phase_index=5,
        input_chain_hash="a" * 64,
        phase_input=b"field",
        phase_output=b"answer",
        public_entrypoint="gravitas-energizer/bin/Energizer.com",
        phase_binary_invoked=True,
    )

    assert receipt["proof_passed"] is False
    assert "public_entrypoint_not_bin_aion_com" in receipt["failed_checks"]
    assert "caller_selected_phase_binary" in receipt["failed_checks"]
