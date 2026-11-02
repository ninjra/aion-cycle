from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "provenance" / "aion-exact-typed-phase-chain-theorem-candidate.py"
SPEC = importlib.util.spec_from_file_location("aion_phase_chain_candidate", MODEL_PATH)
assert SPEC and SPEC.loader
M = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = M
SPEC.loader.exec_module(M)

EPOCH = b"epoch-A"
ENTRYPOINT = "aion-main"


def fixture(proof_profile: bytes = b""):
    route_input = M.CanonicalRouteInput(
        corpus=b"corpus",
        operation_operand=M.TypedValue("Tensor", b"canonical-operation-tensor"),
        selector_binding=b"selector",
        target_namespace_binding=b"target",
        proof_profile_binding=proof_profile,
    )
    route = M.default_route(proof_profile)
    evaluators = M.declared_evaluators(EPOCH, ENTRYPOINT, route, route_input)
    return route, evaluators, route_input


def run_fixture(proof_profile: bytes = b""):
    route, evaluators, route_input = fixture(proof_profile)
    result = M.run_chain(EPOCH, ENTRYPOINT, route, route_input, evaluators)
    assert isinstance(result, M.ChainResult)
    return route, evaluators, route_input, result


def test_fixed_route_closes_both_wire_lifecycles_with_unchanged_operation_echo():
    route, evaluators, route_input, result = run_fixture()
    phase_ids = [phase.phase_id for phase in route]
    assert phase_ids == [row[0] for row in M.MAIN_ROUTE_TYPES]
    assert phase_ids.index("WIRE_DATA_INGRESS") < phase_ids.index("WIRE_DATA_EGRESS")
    assert phase_ids.index("WIRE_OPERATION_INGRESS") < phase_ids.index("WIRE_OPERATION_EGRESS")

    operation_egress = phase_ids.index("WIRE_OPERATION_EGRESS")
    predecessor_value = route_input.typed_value(route)
    for phase in route[: operation_egress + 1]:
        predecessor_value = evaluators[phase.phase_id](predecessor_value)
        assert isinstance(predecessor_value, M.TypedValue)
    state = M.decode_state(predecessor_value)
    assert state["operation_echo"] == state["operation_bytes"]
    assert state["data_d_out"] and state["operation_d_out"]
    assert len(result.links) == len(route)


def test_operation_echo_mutation_rejects_exact_link_verification():
    route, evaluators, route_input = fixture()
    identity = M.route_id(EPOCH, ENTRYPOINT, route, route_input)
    current = route_input.typed_value(route)
    predecessor = M.initial_predecessor(EPOCH, ENTRYPOINT, identity)
    for phase in route:
        next_value = evaluators[phase.phase_id](current)
        assert isinstance(next_value, M.TypedValue)
        if phase.phase_id == "WIRE_OPERATION_EGRESS":
            changed = M.decode_state(next_value)
            changed["operation_echo"] = b"mutated-operation"
            forged = M._state_value(phase.output_type, changed)
            forged_link = M.build_link(
                EPOCH, ENTRYPOINT, identity, phase, len(route), predecessor, current, forged,
            )
            assert M.verify_link(
                EPOCH, ENTRYPOINT, identity, phase, len(route), predecessor,
                current, forged, forged_link, evaluators[phase.phase_id],
            ) == M.Rejected(M.Failure.LINK_MISMATCH)
            return
        link = M.build_link(EPOCH, ENTRYPOINT, identity, phase, len(route), predecessor, current, next_value)
        predecessor, current = link.digest, next_value
    raise AssertionError("operation egress phase not found")


def test_energizer_receipt_binds_foundation_epoch_selector_and_exact_dense_resolve_bytes():
    route, _, route_input, result = run_fixture()
    final = M.decode_state(result.value)
    receipt = M.decode_state(M.TypedValue("ManifestReceipt", final["receipt"]))
    dense = receipt["final_bytes"]
    assert receipt["foundation"] == M.FOUNDATION_B_STAR
    assert receipt["epoch"] == EPOCH
    assert receipt["selector"] == route_input.selector_binding
    assert receipt["final_length"] == len(dense)
    assert receipt["final_sha256"] == M._hash(dense)
    assert final["exact_final_bytes"] == dense
    assert dense.startswith(b"RESOLVED\x00" + route_input.selector_binding + b"\x00")
    assert M.Encode_A is M.CanonicalEncoding_A
    assert M.Decode_A is M.CanonicalDecode_A


@pytest.mark.parametrize(
    "field,bad_value,expected",
    [
        ("foundation", {"patent_sha256": "wrong"}, M.Failure.FOUNDATION_MISMATCH),
        ("epoch", b"wrong-epoch", M.Failure.EPOCH_MISMATCH),
        ("selector", b"wrong-selector", M.Failure.SELECTOR_MISMATCH),
        ("target", b"wrong-target", M.Failure.TARGET_MISMATCH),
        ("final_length", 999, M.Failure.FINAL_BYTES_MISMATCH),
        ("final_sha256", b"x" * 32, M.Failure.FINAL_BYTES_MISMATCH),
    ],
)
def test_close_rejects_each_energizer_receipt_boundary_mutation(field, bad_value, expected):
    route, evaluators, route_input = fixture()
    current = route_input.typed_value(route)
    for phase in route:
        if phase.phase_id == "CLOSE":
            receipt = M.decode_state(current)
            receipt[field] = bad_value
            forged = M._state_value("ManifestReceipt", receipt)
            assert evaluators["CLOSE"](forged) == M.Rejected(expected)
            return
        current = evaluators[phase.phase_id](current)
        assert isinstance(current, M.TypedValue)
    raise AssertionError("close phase not found")


def test_only_fixed_main_route_is_admitted_even_when_alternate_is_well_typed():
    route, evaluators, route_input = fixture()
    fake = list(route)
    fake[6] = replace(fake[6], phase_id="FAKE", operator_binding="operator:FAKE")
    assert M.well_typed(fake)
    assert M.run_chain(EPOCH, ENTRYPOINT, fake, route_input, evaluators) == M.Rejected(M.Failure.ROUTE_MISMATCH)
    bogus = list(route)
    bogus[6] = replace(bogus[6], phase_id="BOGUS", operator_binding="operator:BOGUS")
    assert M.run_chain(EPOCH, ENTRYPOINT, bogus, route_input, evaluators) == M.Rejected(M.Failure.ROUTE_MISMATCH)


def test_v2_route_type_value_and_link_identities_are_one_exact_surface():
    route, _, route_input, result = run_fixture()
    body = M.route_body(EPOCH, ENTRYPOINT, route, route_input)
    assert json.loads(body)["schema"] == "AION-ROUTE-V2"
    assert M.route_id(EPOCH, ENTRYPOINT, route, route_input) == M._hash(b"AION-ROUTE-V2" + body)
    link_body = json.loads(result.links[0].body)
    assert link_body["schema"] == "AION-TYPED-LINK-V2"
    assert link_body["input_type_id_hex"] == M.type_id(EPOCH, route[0].input_type).hex()
    assert link_body["output_type_id_hex"] == M.type_id(EPOCH, route[0].output_type).hex()
    assert "input_type" not in link_body and "output_type" not in link_body
    source = MODEL_PATH.read_text()
    assert "AION-ROUTE-V3" not in source


def test_profile_free_x0_has_no_profile_or_prover_and_no_proof_phases():
    route, _, route_input = fixture()
    initial = route_input.typed_value(route).canonical_bytes
    assert b"profile" not in initial.lower() and b"prover" not in initial.lower()
    assert "PROVE" not in [phase.phase_id for phase in route]
    assert "VERIFY" not in [phase.phase_id for phase in route]


def test_profile_bound_route_has_exact_prove_verify_suffix_and_derived_prover_input():
    route, evaluators, route_input, result = run_fixture(b"proof-profile")
    assert [phase.phase_id for phase in route][-3:] == ["PROVE", "VERIFY", "CLOSE"]
    assert not hasattr(route_input, "prover_input")
    verified = M.verify_chain(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        result.links, result.value, result.terminal_digest,
    )
    assert isinstance(verified, M.VerifiedChain)
    changed_profile = replace(route_input, proof_profile_binding=b"other-profile")
    assert M.verify_chain(
        EPOCH, ENTRYPOINT, route, changed_profile, evaluators,
        result.links, result.value, result.terminal_digest,
    ) == M.Rejected(M.Failure.EVALUATOR_MISMATCH)


def test_profile_phase_insertion_or_removal_rejects():
    route, evaluators, route_input = fixture()
    extra = list(route[:-1]) + list(M.default_route(b"profile")[-3:])
    assert M.run_chain(EPOCH, ENTRYPOINT, extra, route_input, evaluators) == M.Rejected(M.Failure.ROUTE_MISMATCH)
    proof_route, proof_evaluators, proof_input = fixture(b"profile")
    removed = tuple(phase for phase in proof_route if phase.phase_id != "VERIFY")
    assert M.run_chain(EPOCH, ENTRYPOINT, removed, proof_input, proof_evaluators) == M.Rejected(M.Failure.ROUTE_MISMATCH)


def test_actual_callable_identity_rejects_substitution_under_unchanged_label():
    route, evaluators, route_input = fixture()
    substituted = dict(evaluators)
    original = substituted["CALCULATE"]
    substituted["CALCULATE"] = lambda value: original(value)
    assert M.run_chain(EPOCH, ENTRYPOINT, route, route_input, substituted) == M.Rejected(M.Failure.EVALUATOR_MISMATCH)


@pytest.mark.parametrize(
    "mutation",
    [
        {"epoch": b"other-epoch"},
        {"entrypoint": "other-entrypoint"},
        {"route_identity": b"x" * 32},
    ],
)
def test_same_callable_with_substituted_evaluator_environment_rejects(mutation):
    route, evaluators, route_input = fixture()
    substituted = dict(evaluators)
    substituted["CALCULATE"] = replace(substituted["CALCULATE"], **mutation)
    assert M.run_chain(EPOCH, ENTRYPOINT, route, route_input, substituted) == M.Rejected(M.Failure.EVALUATOR_MISMATCH)


def test_same_callable_with_substituted_route_input_rejects():
    route, evaluators, route_input = fixture()
    substituted = dict(evaluators)
    changed_input = replace(route_input, selector_binding=b"other-selector")
    substituted["CALCULATE"] = replace(substituted["CALCULATE"], route_input=changed_input)
    assert M.run_chain(EPOCH, ENTRYPOINT, route, route_input, substituted) == M.Rejected(M.Failure.EVALUATOR_MISMATCH)


def test_malformed_route_input_returns_typed_rejection():
    route, evaluators, route_input = fixture()
    malformed = replace(route_input, selector_binding="not-bytes")
    assert M.run_chain(EPOCH, ENTRYPOINT, route, malformed, evaluators) == M.Rejected(M.Failure.TYPE_MISMATCH)


def test_standalone_link_rejects_forged_declaration_and_route_identity():
    route, evaluators, route_input, result = run_fixture()
    initial = route_input.typed_value(route)
    identity = M.route_id(EPOCH, ENTRYPOINT, route, route_input)
    predecessor = M.initial_predecessor(EPOCH, ENTRYPOINT, identity)
    output = evaluators[route[0].phase_id](initial)
    assert isinstance(output, M.TypedValue)
    forged_phase = replace(route[0], operator_binding="operator:FAKE")
    forged_link = M.build_link(
        EPOCH, ENTRYPOINT, b"x" * 32, forged_phase, len(route),
        predecessor, initial, output,
    )
    assert M.verify_link(
        EPOCH, ENTRYPOINT, b"x" * 32, forged_phase, len(route), predecessor,
        initial, output, forged_link, evaluators[route[0].phase_id],
    ) == M.Rejected(M.Failure.ROUTE_MISMATCH)


def test_standalone_link_malformed_arguments_return_typed_rejection():
    route, evaluators, route_input, result = run_fixture()
    initial = route_input.typed_value(route)
    identity = M.route_id(EPOCH, ENTRYPOINT, route, route_input)
    output = evaluators[route[0].phase_id](initial)
    assert isinstance(output, M.TypedValue)
    assert M.verify_link(
        EPOCH, ENTRYPOINT, identity, route[0], len(route), "not-bytes",
        initial, output, result.links[0], evaluators[route[0].phase_id],
    ) == M.Rejected(M.Failure.TYPE_MISMATCH)


@pytest.mark.parametrize(
    "failure",
    [M.Failure.TIMEOUT, M.Failure.UNAVAILABLE, M.Failure.EXCEPTION, M.Failure.SEMANTIC_FAILURE],
)
def test_timeout_unavailable_exception_and_semantic_failure_are_typed_rejections(failure):
    route, evaluators, route_input = fixture()
    changed = dict(evaluators)
    changed["CALCULATE"] = M.with_failure(changed["CALCULATE"], failure)
    assert M.run_chain(EPOCH, ENTRYPOINT, route, route_input, changed) == M.Rejected(failure)


def test_verify_link_and_verify_chain_return_typed_results_not_booleans():
    route, evaluators, route_input, result = run_fixture()
    initial = route_input.typed_value(route)
    identity = M.route_id(EPOCH, ENTRYPOINT, route, route_input)
    predecessor = M.initial_predecessor(EPOCH, ENTRYPOINT, identity)
    output = evaluators[route[0].phase_id](initial)
    assert isinstance(output, M.TypedValue)
    link_result = M.verify_link(
        EPOCH, ENTRYPOINT, identity, route[0], len(route), predecessor,
        initial, output, result.links[0], evaluators[route[0].phase_id],
    )
    assert isinstance(link_result, M.VerifiedLink) and not isinstance(link_result, bool)
    chain_result = M.verify_chain(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        result.links, result.value, result.terminal_digest,
    )
    assert isinstance(chain_result, M.VerifiedChain) and not isinstance(chain_result, bool)


def test_whole_chain_rejects_link_terminal_epoch_entrypoint_and_bound_input_mutations():
    route, evaluators, route_input, result = run_fixture()
    changed_links = list(result.links)
    changed_links[3] = replace(changed_links[3], body=changed_links[3].body + b" ")
    assert M.verify_chain(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        changed_links, result.value, result.terminal_digest,
    ) == M.Rejected(M.Failure.LINK_MISMATCH)
    assert isinstance(M.verify_chain(
        b"other-epoch", ENTRYPOINT, route, route_input, evaluators,
        result.links, result.value, result.terminal_digest,
    ), M.Rejected)
    assert isinstance(M.verify_chain(
        EPOCH, "other-entry", route, route_input, evaluators,
        result.links, result.value, result.terminal_digest,
    ), M.Rejected)
    for mutation in (
        replace(route_input, operation_operand=M.TypedValue("Tensor", b"other-operation")),
        replace(route_input, selector_binding=b"other-selector"),
        replace(route_input, target_namespace_binding=b"other-target"),
    ):
        assert isinstance(M.verify_chain(
            EPOCH, ENTRYPOINT, route, mutation, evaluators,
            result.links, result.value, result.terminal_digest,
        ), M.Rejected)
    terminal = M.TypedValue(result.value.type_name, result.value.canonical_bytes + b"!")
    assert M.verify_chain(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        result.links, terminal, result.terminal_digest,
    ) == M.Rejected(M.Failure.TERMINAL_MISMATCH)


def test_present_verified_prefix_section_matches_whole_chain_and_mutation_rejects():
    route, evaluators, route_input, result = run_fixture()
    split = 6
    section = M.verify_section(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        result.links[:split], result.links[split:],
    )
    assert isinstance(section, M.SectionResult)
    assert section.value == result.value
    assert section.terminal_digest == result.terminal_digest
    changed_prefix = list(result.links[:split])
    changed_prefix[-1] = replace(changed_prefix[-1], digest=b"x" * 32)
    assert M.verify_section(
        EPOCH, ENTRYPOINT, route, route_input, evaluators,
        changed_prefix, result.links[split:],
    ) == M.Rejected(M.Failure.PREFIX_MISMATCH)


def test_model_exposes_no_boundary_vector_source_ledger_or_v3_identity():
    text = MODEL_PATH.read_text()
    for forbidden in ("source_record_id", "field_to_records", "boundary_values", "AION-ROUTE-V3"):
        assert forbidden not in text
    assert "VerifiedPrefixAnchor" in text
    assert "input_type_id_hex" in text
