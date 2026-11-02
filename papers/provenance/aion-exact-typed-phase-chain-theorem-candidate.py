"""Executable candidate for the Paper V exact typed phase-chain theorem.

The model is intentionally paper-local.  It fixes the only admitted route,
canonical V2 identities, two complete Wire lifecycles, dense Resolve and
Energizer receipt checks, evaluator/callable identity, typed failure
propagation, optional profile-bound proof phases, and present-prefix section
verification.  It does not implement any companion owner theorem and grants
no implementation-equivalence or publication authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
from types import CodeType
from typing import Callable, Mapping, Sequence


class Failure(str, Enum):
    REJECT = "REJECT"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    ROUTE_MISMATCH = "ROUTE_MISMATCH"
    PROFILE_MISMATCH = "PROFILE_MISMATCH"
    EVALUATOR_MISMATCH = "EVALUATOR_MISMATCH"
    RELATION_REJECTED = "RELATION_REJECTED"
    SEMANTIC_FAILURE = "SEMANTIC_FAILURE"
    TIMEOUT = "TIMEOUT"
    UNAVAILABLE = "UNAVAILABLE"
    EXCEPTION = "EXCEPTION"
    LINK_MISMATCH = "LINK_MISMATCH"
    CHAIN_LENGTH = "CHAIN_LENGTH"
    TERMINAL_MISMATCH = "TERMINAL_MISMATCH"
    PREFIX_MISMATCH = "PREFIX_MISMATCH"
    WIRE_STATE = "WIRE_STATE"
    OPERATION_ECHO_MISMATCH = "OPERATION_ECHO_MISMATCH"
    FOUNDATION_MISMATCH = "FOUNDATION_MISMATCH"
    EPOCH_MISMATCH = "EPOCH_MISMATCH"
    SELECTOR_MISMATCH = "SELECTOR_MISMATCH"
    TARGET_MISMATCH = "TARGET_MISMATCH"
    FINAL_BYTES_MISMATCH = "FINAL_BYTES_MISMATCH"


@dataclass(frozen=True)
class TypedValue:
    type_name: str
    canonical_bytes: bytes


@dataclass(frozen=True)
class CanonicalRouteInput:
    corpus: bytes
    operation_operand: TypedValue
    selector_binding: bytes
    target_namespace_binding: bytes
    proof_profile_binding: bytes = b""

    def typed_value(self, route: Sequence["PhaseDeclaration"]) -> TypedValue:
        if not route or self.operation_operand.type_name != "Tensor":
            raise ValueError("route input requires one canonical Tensor operation operand")
        # Proof profile and prover input are declaration data, never X0 values.
        return _state_value(route[0].input_type, {
            "corpus": self.corpus,
            "operation_tensor": self.operation_operand.canonical_bytes,
            "selector": self.selector_binding,
            "target": self.target_namespace_binding,
        })


@dataclass(frozen=True)
class PhaseDeclaration:
    phase_id: str
    index: int
    input_type: str
    output_type: str
    operator_binding: str
    evaluator_binding: str


@dataclass(frozen=True)
class Link:
    body: bytes
    digest: bytes


@dataclass(frozen=True)
class ChainResult:
    value: TypedValue
    terminal_digest: bytes
    links: tuple[Link, ...]


@dataclass(frozen=True)
class VerifiedLink:
    digest: bytes


@dataclass(frozen=True)
class VerifiedChain:
    value: TypedValue
    terminal_digest: bytes


@dataclass(frozen=True)
class PrefixVerificationReceipt:
    digest: bytes


@dataclass(frozen=True)
class VerifiedPrefixAnchor:
    route_identity: bytes
    epoch: bytes
    entrypoint: str
    predecessor_index: int
    boundary_value: TypedValue
    predecessor_digest: bytes
    receipt: PrefixVerificationReceipt


@dataclass(frozen=True)
class SectionResult:
    value: TypedValue
    terminal_digest: bytes
    anchor: VerifiedPrefixAnchor


@dataclass(frozen=True)
class Rejected:
    failure: Failure


FOUNDATION_B_STAR = {
    "patent_sha256": "e2975c587ae6299f86a84e4630c51a4de19b72abfaf4ec45c853f68775418240",
    "ionizer_sha256": "bf58f880e75aa4e62052bcefd59ce6c4fd44e80dcd941042f66e124e65de3efe",
    "catalog_sha256": "768f68a9c67dbf3a9be8ceaa251350dcd63ab59eb8ef4b6902a13b633613796d",
}

MAIN_ROUTE_TYPES: tuple[tuple[str, str, str], ...] = (
    ("IONIZE", "Corpus*Operation*Selector*Target", "Tensor*Operation*Selector*Target"),
    ("ENCODE_DATA", "Tensor*Operation*Selector*Target", "Bytes*Operation*Selector*Target"),
    ("WIRE_DATA_INGRESS", "Bytes*Operation*Selector*Target", "Bytes*Operation*Selector*Target*DataIngressState"),
    ("ENCODE_OPERATION", "Bytes*Operation*Selector*Target*DataIngressState", "Bytes*Bytes*Selector*Target*DataIngressState"),
    ("WIRE_OPERATION_INGRESS", "Bytes*Bytes*Selector*Target*DataIngressState", "Bytes*Bytes*Selector*Target*DataIngressState*OperationIngressState"),
    ("DECODE_OPERANDS", "Bytes*Bytes*Selector*Target*DataIngressState*OperationIngressState", "Tensor*Tensor*Bytes*Selector*Target*DataIngressState*OperationIngressState"),
    ("CALCULATE", "Tensor*Tensor*Bytes*Selector*Target*DataIngressState*OperationIngressState", "Tensor*Bytes*Selector*Target*DataIngressState*OperationIngressState"),
    ("ENCODE_RESULT", "Tensor*Bytes*Selector*Target*DataIngressState*OperationIngressState", "Bytes*Bytes*Selector*Target*DataIngressState*OperationIngressState"),
    ("WIRE_DATA_EGRESS", "Bytes*Bytes*Selector*Target*DataIngressState*OperationIngressState", "Bytes*Bytes*Selector*Target*DataEgressState*OperationIngressState"),
    ("WIRE_OPERATION_EGRESS", "Bytes*Bytes*Selector*Target*DataEgressState*OperationIngressState", "Bytes*Bytes*Selector*Target*DataEgressState*OperationEgressState"),
    ("DECODE_RESULT", "Bytes*Bytes*Selector*Target*DataEgressState*OperationEgressState", "Tensor*Selector*Target"),
    ("RESOLVE", "Tensor*Selector*Target", "Tensor*Selector*Target*Corpus"),
    ("MANIFEST", "Tensor*Selector*Target*Corpus", "ManifestReceipt"),
    ("CLOSE", "ManifestReceipt", "RouteResult"),
)


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _record(fields: Mapping[str, object]) -> bytes:
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _encode_fields(fields: Mapping[str, bytes | str | int | Mapping[str, str]]) -> dict[str, object]:
    encoded: dict[str, object] = {}
    for key, value in fields.items():
        if isinstance(value, bytes):
            encoded[key + "_hex"] = value.hex()
        else:
            encoded[key] = value
    return encoded


def _state_value(type_name: str, fields: Mapping[str, bytes | str | int | Mapping[str, str]]) -> TypedValue:
    return TypedValue(type_name, _record(_encode_fields(fields)))


def decode_state(value: TypedValue) -> dict[str, object]:
    raw = json.loads(value.canonical_bytes.decode("utf-8"))
    state: dict[str, object] = {}
    for key, item in raw.items():
        if key.endswith("_hex") and isinstance(item, str):
            state[key[:-4]] = bytes.fromhex(item)
        else:
            state[key] = item
    return state


def CanonicalEncoding_A(tensor: bytes) -> bytes:
    return b"IONIZER-CANONICAL-V1\x00" + len(tensor).to_bytes(8, "big") + tensor


def CanonicalDecode_A(encoded: bytes) -> bytes | Rejected:
    prefix = b"IONIZER-CANONICAL-V1\x00"
    if not encoded.startswith(prefix) or len(encoded) < len(prefix) + 8:
        return Rejected(Failure.TYPE_MISMATCH)
    size = int.from_bytes(encoded[len(prefix):len(prefix) + 8], "big")
    payload = encoded[len(prefix) + 8:]
    if len(payload) != size:
        return Rejected(Failure.TYPE_MISMATCH)
    return payload


Encode_A = CanonicalEncoding_A
Decode_A = CanonicalDecode_A


def Phi_A(corpus: bytes) -> bytes:
    return _hash(b"IONIZER-PHI-CANDIDATE-V1" + corpus)


def Calculate_A(data_tensor: bytes, operation_tensor: bytes) -> bytes:
    return _hash(b"CALCULATE-CANDIDATE-V1" + data_tensor + operation_tensor)


def Resolve_A(result_tensor: bytes, selector: bytes) -> bytes:
    # Dense selected-result boundary.  This is not an Ionizer implementation.
    return b"RESOLVED\x00" + selector + b"\x00" + result_tensor


def _wire_in(epoch: bytes, payload: bytes) -> tuple[bytes, bytes, bytes]:
    rho = _hash(b"WIRE-ROUTE-V1" + epoch + _hash(payload))
    d_in = _hash(b"WIRE-INGRESS-V1" + epoch + rho + payload)
    return payload, rho, d_in


def _wire_out(epoch: bytes, rho: bytes, d_in: bytes, payload: bytes) -> tuple[bytes, bytes]:
    return payload, _hash(b"WIRE-EGRESS-V1" + epoch + rho + d_in + payload)


def _code_identity(code: CodeType, owner: str, phase_id: str) -> bytes:
    return _hash(
        b"AION-EVALUATOR-CALLABLE-V2"
        + owner.encode()
        + phase_id.encode()
        + code.co_code
        + repr(code.co_consts).encode()
        + repr(code.co_names).encode()
    )


def _declared_evaluator_binding(phase_id: str) -> str:
    return _code_identity(PhaseEvaluator.__call__.__code__, "PhaseEvaluator.__call__", phase_id).hex()


def evaluator_identity(evaluator: object) -> str:
    if type(evaluator) is PhaseEvaluator:
        return _code_identity(PhaseEvaluator.__call__.__code__, "PhaseEvaluator.__call__", evaluator.phase_id).hex()
    call: object = evaluator
    if not hasattr(call, "__code__") and hasattr(call, "__call__"):
        call = call.__call__
    code = getattr(call, "__code__", None)
    if not isinstance(code, CodeType):
        return _hash(b"AION-EVALUATOR-UNKNOWN-V2" + repr(type(evaluator)).encode()).hex()
    return _code_identity(code, getattr(call, "__qualname__", type(evaluator).__qualname__), "UNKNOWN").hex()


def default_route(proof_profile_binding: bytes = b"") -> tuple[PhaseDeclaration, ...]:
    types = list(MAIN_ROUTE_TYPES)
    if proof_profile_binding:
        types[-1:] = [
            ("PROVE", "ManifestReceipt", "ManifestReceipt*Statement*ProofBytes"),
            ("VERIFY", "ManifestReceipt*Statement*ProofBytes", "ManifestReceipt*VerifiedStatement"),
            ("CLOSE", "ManifestReceipt*VerifiedStatement", "RouteResult"),
        ]
    return tuple(
        PhaseDeclaration(
            phase_id,
            index,
            input_type,
            output_type,
            _hash(b"AION-OPERATOR-V2" + phase_id.encode()).hex(),
            _declared_evaluator_binding(phase_id),
        )
        for index, (phase_id, input_type, output_type) in enumerate(types)
    )


def well_typed(route: Sequence[PhaseDeclaration]) -> bool:
    if not route or not all(isinstance(phase, PhaseDeclaration) for phase in route):
        return False
    return all(
        phase.index == index
        and (index == len(route) - 1 or phase.output_type == route[index + 1].input_type)
        for index, phase in enumerate(route)
    )


def fixed_route(route: Sequence[PhaseDeclaration], proof_profile_binding: bytes) -> bool:
    return isinstance(proof_profile_binding, bytes) and tuple(route) == default_route(proof_profile_binding)


def valid_route_input(route_input: object) -> bool:
    return (
        isinstance(route_input, CanonicalRouteInput)
        and isinstance(route_input.corpus, bytes)
        and isinstance(route_input.operation_operand, TypedValue)
        and isinstance(route_input.operation_operand.type_name, str)
        and isinstance(route_input.operation_operand.canonical_bytes, bytes)
        and isinstance(route_input.selector_binding, bytes)
        and isinstance(route_input.target_namespace_binding, bytes)
        and isinstance(route_input.proof_profile_binding, bytes)
    )


def type_id(epoch: bytes, type_name: str) -> bytes:
    canonical_description = _record({"type": type_name})
    return _hash(b"AION-TYPE-V2" + epoch + canonical_description)


def value_id(epoch: bytes, value: TypedValue) -> bytes:
    return _hash(
        b"AION-VALUE-V2"
        + epoch
        + type_id(epoch, value.type_name)
        + value.canonical_bytes
    )


def route_body(epoch: bytes, entrypoint: str, route: Sequence[PhaseDeclaration], route_input: CanonicalRouteInput) -> bytes:
    phases = [
        {
            "phase_id": phase.phase_id,
            "phase_index": phase.index,
            "input_type_id_hex": type_id(epoch, phase.input_type).hex(),
            "output_type_id_hex": type_id(epoch, phase.output_type).hex(),
            "operator_binding": phase.operator_binding,
            "evaluator_binding": phase.evaluator_binding,
        }
        for phase in route
    ]
    return _record({
        "schema": "AION-ROUTE-V2",
        "epoch_hex": epoch.hex(),
        "entrypoint": entrypoint,
        "phases": phases,
        "operation_value_id_hex": value_id(epoch, route_input.operation_operand).hex(),
        "wire_routes": ["DATA:W_in,A->W_out,A", "OPERATION:W_in,A->W_out,A:UNCHANGED_ECHO"],
        "selector_hex": route_input.selector_binding.hex(),
        "target_namespace_hex": route_input.target_namespace_binding.hex(),
        "proof_profile_hex": route_input.proof_profile_binding.hex(),
    })


def route_id(epoch: bytes, entrypoint: str, route: Sequence[PhaseDeclaration], route_input: CanonicalRouteInput) -> bytes:
    return _hash(b"AION-ROUTE-V2" + route_body(epoch, entrypoint, route, route_input))


def initial_predecessor(epoch: bytes, entrypoint: str, route_identity: bytes) -> bytes:
    return _hash(b"AION-CHAIN-START-V2" + route_identity + epoch + entrypoint.encode())


def build_link(
    epoch: bytes,
    entrypoint: str,
    route_identity: bytes,
    phase: PhaseDeclaration,
    chain_length: int,
    predecessor: bytes,
    input_value: TypedValue,
    output_value: TypedValue,
) -> Link:
    body = _record({
        "schema": "AION-TYPED-LINK-V2",
        "epoch_hex": epoch.hex(),
        "entrypoint": entrypoint,
        "route_hex": route_identity.hex(),
        "phase_id": phase.phase_id,
        "phase_index": phase.index,
        "chain_length": chain_length,
        "input_type_id_hex": type_id(epoch, phase.input_type).hex(),
        "output_type_id_hex": type_id(epoch, phase.output_type).hex(),
        "operator_binding": phase.operator_binding,
        "evaluator_binding": phase.evaluator_binding,
        "predecessor_hex": predecessor.hex(),
        "input_identity_hex": value_id(epoch, input_value).hex(),
        "output_identity_hex": value_id(epoch, output_value).hex(),
        "status": "OK",
    })
    return Link(body, _hash(b"AION-TYPED-LINK-DIGEST-V2" + body))


@dataclass(frozen=True)
class PhaseEvaluator:
    phase_id: str
    epoch: bytes
    entrypoint: str
    route_identity: bytes
    route_input: CanonicalRouteInput
    forced_failure: Failure | None = None
    raise_timeout: bool = False
    raise_unavailable: bool = False
    raise_exception: bool = False

    def __call__(self, value: TypedValue) -> TypedValue | Rejected:
        if self.raise_timeout:
            raise TimeoutError("declared evaluator timeout")
        if self.raise_unavailable:
            raise ConnectionError("declared evaluator unavailable")
        if self.raise_exception:
            raise RuntimeError("declared evaluator exception")
        if self.forced_failure is not None:
            return Rejected(self.forced_failure)
        return _evaluate_phase(self, value)


Evaluator = Callable[[TypedValue], TypedValue | Rejected]


def _evaluate_phase(evaluator: PhaseEvaluator, value: TypedValue) -> TypedValue | Rejected:
    try:
        s = decode_state(value)
    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
        return Rejected(Failure.TYPE_MISMATCH)
    p = evaluator.phase_id
    epoch = evaluator.epoch
    out = default_route(evaluator.route_input.proof_profile_binding)
    phase = next((item for item in out if item.phase_id == p), None)
    if phase is None or value.type_name != phase.input_type:
        return Rejected(Failure.TYPE_MISMATCH)

    if p == "IONIZE":
        return _state_value(phase.output_type, {
            "data_tensor": Phi_A(s["corpus"]), "operation_tensor": s["operation_tensor"],
            "selector": s["selector"], "target": s["target"],
        })
    if p == "ENCODE_DATA":
        return _state_value(phase.output_type, {
            "data_bytes": Encode_A(s["data_tensor"]), "operation_tensor": s["operation_tensor"],
            "selector": s["selector"], "target": s["target"],
        })
    if p == "WIRE_DATA_INGRESS":
        b_in, rho, d_in = _wire_in(epoch, s["data_bytes"])
        if b_in != s["data_bytes"]:
            return Rejected(Failure.WIRE_STATE)
        return _state_value(phase.output_type, {
            **s, "data_rho": rho, "data_d_in": d_in,
        })
    if p == "ENCODE_OPERATION":
        return _state_value(phase.output_type, {
            "data_bytes": s["data_bytes"], "operation_bytes": Encode_A(s["operation_tensor"]),
            "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"],
        })
    if p == "WIRE_OPERATION_INGRESS":
        b_in, rho, d_in = _wire_in(epoch, s["operation_bytes"])
        if b_in != s["operation_bytes"]:
            return Rejected(Failure.WIRE_STATE)
        return _state_value(phase.output_type, {
            **s, "operation_rho": rho, "operation_d_in": d_in,
        })
    if p == "DECODE_OPERANDS":
        data_tensor = Decode_A(s["data_bytes"])
        operation_tensor = Decode_A(s["operation_bytes"])
        if isinstance(data_tensor, Rejected) or isinstance(operation_tensor, Rejected):
            return Rejected(Failure.TYPE_MISMATCH)
        return _state_value(phase.output_type, {
            "data_tensor": data_tensor, "operation_tensor": operation_tensor,
            "operation_bytes": s["operation_bytes"], "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"],
            "operation_rho": s["operation_rho"], "operation_d_in": s["operation_d_in"],
        })
    if p == "CALCULATE":
        return _state_value(phase.output_type, {
            "result_tensor": Calculate_A(s["data_tensor"], s["operation_tensor"]),
            "operation_bytes": s["operation_bytes"], "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"],
            "operation_rho": s["operation_rho"], "operation_d_in": s["operation_d_in"],
        })
    if p == "ENCODE_RESULT":
        return _state_value(phase.output_type, {
            "result_bytes": Encode_A(s["result_tensor"]), "operation_bytes": s["operation_bytes"],
            "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"],
            "operation_rho": s["operation_rho"], "operation_d_in": s["operation_d_in"],
        })
    if p == "WIRE_DATA_EGRESS":
        b_out, d_out = _wire_out(epoch, s["data_rho"], s["data_d_in"], s["result_bytes"])
        if b_out != s["result_bytes"]:
            return Rejected(Failure.WIRE_STATE)
        return _state_value(phase.output_type, {
            "result_bytes": b_out, "operation_bytes": s["operation_bytes"],
            "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"], "data_d_out": d_out,
            "operation_rho": s["operation_rho"], "operation_d_in": s["operation_d_in"],
        })
    if p == "WIRE_OPERATION_EGRESS":
        echo, d_out = _wire_out(epoch, s["operation_rho"], s["operation_d_in"], s["operation_bytes"])
        if echo != s["operation_bytes"]:
            return Rejected(Failure.OPERATION_ECHO_MISMATCH)
        return _state_value(phase.output_type, {
            "result_bytes": s["result_bytes"], "operation_bytes": s["operation_bytes"],
            "operation_echo": echo, "selector": s["selector"], "target": s["target"],
            "data_rho": s["data_rho"], "data_d_in": s["data_d_in"], "data_d_out": s["data_d_out"],
            "operation_rho": s["operation_rho"], "operation_d_in": s["operation_d_in"],
            "operation_d_out": d_out,
        })
    if p == "DECODE_RESULT":
        if s["operation_echo"] != s["operation_bytes"]:
            return Rejected(Failure.OPERATION_ECHO_MISMATCH)
        tensor = Decode_A(s["result_bytes"])
        if isinstance(tensor, Rejected):
            return tensor
        return _state_value(phase.output_type, {
            "result_tensor": tensor, "selector": s["selector"], "target": s["target"],
        })
    if p == "RESOLVE":
        dense = Resolve_A(s["result_tensor"], s["selector"])
        return _state_value(phase.output_type, {
            "result_tensor": s["result_tensor"], "selector": s["selector"], "target": s["target"],
            "selected_dense_bytes": dense,
        })
    if p == "MANIFEST":
        dense = s["selected_dense_bytes"]
        return _state_value(phase.output_type, {
            "target": s["target"], "final_bytes": dense, "final_length": len(dense),
            "final_sha256": _hash(dense), "foundation": FOUNDATION_B_STAR,
            "epoch": epoch, "selector": s["selector"],
        })
    if p == "PROVE":
        profile = evaluator.route_input.proof_profile_binding
        if not profile:
            return Rejected(Failure.PROFILE_MISMATCH)
        statement = _hash(b"AION-STATEMENT-V2" + evaluator.route_identity + value.canonical_bytes + profile)
        prover_input = _hash(b"AION-PROVER-INPUT-V2" + profile)
        proof = _hash(b"AION-PROOF-V2" + evaluator.route_identity + statement + prover_input)
        return _state_value(phase.output_type, {
            "receipt": value.canonical_bytes, "statement": statement, "proof": proof,
        })
    if p == "VERIFY":
        profile = evaluator.route_input.proof_profile_binding
        if not profile:
            return Rejected(Failure.PROFILE_MISMATCH)
        expected = _hash(
            b"AION-PROOF-V2" + evaluator.route_identity + s["statement"]
            + _hash(b"AION-PROVER-INPUT-V2" + profile)
        )
        if s["proof"] != expected:
            return Rejected(Failure.SEMANTIC_FAILURE)
        return _state_value(phase.output_type, {
            "receipt": s["receipt"], "verified_statement": s["statement"],
        })
    if p == "CLOSE":
        receipt_bytes = s.get("receipt", value.canonical_bytes)
        try:
            receipt = decode_state(TypedValue("ManifestReceipt", receipt_bytes))
        except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            return Rejected(Failure.TYPE_MISMATCH)
        dense = receipt.get("final_bytes")
        if receipt.get("foundation") != FOUNDATION_B_STAR:
            return Rejected(Failure.FOUNDATION_MISMATCH)
        if receipt.get("epoch") != epoch:
            return Rejected(Failure.EPOCH_MISMATCH)
        if receipt.get("selector") != evaluator.route_input.selector_binding:
            return Rejected(Failure.SELECTOR_MISMATCH)
        if receipt.get("target") != evaluator.route_input.target_namespace_binding:
            return Rejected(Failure.TARGET_MISMATCH)
        if not isinstance(dense, bytes) or receipt.get("final_length") != len(dense):
            return Rejected(Failure.FINAL_BYTES_MISMATCH)
        if receipt.get("final_sha256") != _hash(dense):
            return Rejected(Failure.FINAL_BYTES_MISMATCH)
        return _state_value(phase.output_type, {
            "receipt": receipt_bytes, "exact_final_bytes": dense,
        })
    return Rejected(Failure.ROUTE_MISMATCH)


def declared_evaluators(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
) -> dict[str, PhaseEvaluator]:
    identity = route_id(epoch, entrypoint, route, route_input)
    return {
        phase.phase_id: PhaseEvaluator(phase.phase_id, epoch, entrypoint, identity, route_input)
        for phase in route
    }


def _safe_evaluate(
    phase: PhaseDeclaration,
    evaluator: Evaluator,
    value: TypedValue,
    *,
    epoch: bytes,
    entrypoint: str,
    route_identity: bytes,
    route_input: CanonicalRouteInput,
) -> TypedValue | Rejected:
    if (
        not isinstance(phase, PhaseDeclaration)
        or not isinstance(value, TypedValue)
        or not isinstance(epoch, bytes)
        or not isinstance(entrypoint, str)
        or not isinstance(route_identity, bytes)
        or not valid_route_input(route_input)
    ):
        return Rejected(Failure.TYPE_MISMATCH)
    if evaluator_identity(evaluator) != phase.evaluator_binding:
        return Rejected(Failure.EVALUATOR_MISMATCH)
    if type(evaluator) is not PhaseEvaluator:
        return Rejected(Failure.EVALUATOR_MISMATCH)
    if (
        evaluator.phase_id != phase.phase_id
        or evaluator.epoch != epoch
        or evaluator.entrypoint != entrypoint
        or evaluator.route_identity != route_identity
        or evaluator.route_input != route_input
    ):
        return Rejected(Failure.EVALUATOR_MISMATCH)
    canonical_route = default_route(route_input.proof_profile_binding)
    if (
        phase.index < 0
        or phase.index >= len(canonical_route)
        or phase != canonical_route[phase.index]
    ):
        return Rejected(Failure.ROUTE_MISMATCH)
    try:
        expected_route_identity = route_id(epoch, entrypoint, canonical_route, route_input)
    except (AttributeError, TypeError, ValueError):
        return Rejected(Failure.TYPE_MISMATCH)
    if route_identity != expected_route_identity:
        return Rejected(Failure.ROUTE_MISMATCH)
    try:
        result = evaluator(value)
    except TimeoutError:
        return Rejected(Failure.TIMEOUT)
    except ConnectionError:
        return Rejected(Failure.UNAVAILABLE)
    except Exception:
        return Rejected(Failure.EXCEPTION)
    if isinstance(result, Rejected):
        return result
    if not isinstance(result, TypedValue):
        return Rejected(Failure.TYPE_MISMATCH)
    if value.type_name != phase.input_type or result.type_name != phase.output_type:
        return Rejected(Failure.TYPE_MISMATCH)
    return result


def verify_link(
    epoch: bytes,
    entrypoint: str,
    route_identity: bytes,
    phase: PhaseDeclaration,
    chain_length: int,
    predecessor: bytes,
    input_value: TypedValue,
    output_value: TypedValue,
    link: Link,
    evaluator: Evaluator,
) -> VerifiedLink | Rejected:
    if (
        not isinstance(epoch, bytes)
        or not isinstance(entrypoint, str)
        or not isinstance(route_identity, bytes)
        or not isinstance(phase, PhaseDeclaration)
        or not isinstance(chain_length, int)
        or chain_length < 1
        or not isinstance(predecessor, bytes)
        or not isinstance(input_value, TypedValue)
        or not isinstance(output_value, TypedValue)
        or not isinstance(link, Link)
        or not isinstance(link.body, bytes)
        or not isinstance(link.digest, bytes)
    ):
        return Rejected(Failure.TYPE_MISMATCH)
    if type(evaluator) is not PhaseEvaluator or not valid_route_input(evaluator.route_input):
        return Rejected(Failure.EVALUATOR_MISMATCH)
    canonical_route = default_route(evaluator.route_input.proof_profile_binding)
    if (
        chain_length != len(canonical_route)
        or phase.index < 0
        or phase.index >= len(canonical_route)
        or phase != canonical_route[phase.index]
    ):
        return Rejected(Failure.ROUTE_MISMATCH)
    fresh = _safe_evaluate(
        phase, evaluator, input_value,
        epoch=epoch,
        entrypoint=entrypoint,
        route_identity=route_identity,
        route_input=evaluator.route_input,
    )
    if isinstance(fresh, Rejected):
        return fresh
    if fresh != output_value:
        return Rejected(Failure.LINK_MISMATCH)
    expected = build_link(
        epoch, entrypoint, route_identity, phase, chain_length,
        predecessor, input_value, output_value,
    )
    if link != expected:
        return Rejected(Failure.LINK_MISMATCH)
    return VerifiedLink(link.digest)


def _identity_and_initial(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
) -> tuple[bytes, TypedValue] | Rejected:
    if (
        not isinstance(epoch, bytes)
        or not isinstance(entrypoint, str)
        or not valid_route_input(route_input)
    ):
        return Rejected(Failure.TYPE_MISMATCH)
    if not well_typed(route) or not fixed_route(route, route_input.proof_profile_binding):
        return Rejected(Failure.ROUTE_MISMATCH)
    try:
        initial = route_input.typed_value(route)
        identity = route_id(epoch, entrypoint, route, route_input)
    except (AttributeError, TypeError, ValueError):
        return Rejected(Failure.TYPE_MISMATCH)
    return identity, initial


def run_chain(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
    evaluators: Mapping[str, Evaluator],
) -> ChainResult | Rejected:
    prepared = _identity_and_initial(epoch, entrypoint, route, route_input)
    if isinstance(prepared, Rejected):
        return prepared
    identity, current = prepared
    predecessor = initial_predecessor(epoch, entrypoint, identity)
    links: list[Link] = []
    for phase in route:
        evaluator = evaluators.get(phase.phase_id)
        if evaluator is None:
            return Rejected(Failure.UNAVAILABLE)
        next_value = _safe_evaluate(
            phase, evaluator, current,
            epoch=epoch, entrypoint=entrypoint,
            route_identity=identity, route_input=route_input,
        )
        if isinstance(next_value, Rejected):
            return next_value
        link = build_link(epoch, entrypoint, identity, phase, len(route), predecessor, current, next_value)
        verified = verify_link(
            epoch, entrypoint, identity, phase, len(route), predecessor,
            current, next_value, link, evaluator,
        )
        if isinstance(verified, Rejected):
            return verified
        links.append(link)
        predecessor = link.digest
        current = next_value
    return ChainResult(current, predecessor, tuple(links))


def verify_chain(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
    evaluators: Mapping[str, Evaluator],
    links: Sequence[Link],
    terminal_value: TypedValue,
    terminal_digest: bytes,
) -> VerifiedChain | Rejected:
    prepared = _identity_and_initial(epoch, entrypoint, route, route_input)
    if isinstance(prepared, Rejected):
        return prepared
    if len(links) != len(route):
        return Rejected(Failure.CHAIN_LENGTH)
    identity, current = prepared
    predecessor = initial_predecessor(epoch, entrypoint, identity)
    for phase, link in zip(route, links, strict=True):
        evaluator = evaluators.get(phase.phase_id)
        if evaluator is None:
            return Rejected(Failure.UNAVAILABLE)
        next_value = _safe_evaluate(
            phase, evaluator, current,
            epoch=epoch, entrypoint=entrypoint,
            route_identity=identity, route_input=route_input,
        )
        if isinstance(next_value, Rejected):
            return next_value
        verified = verify_link(
            epoch, entrypoint, identity, phase, len(route), predecessor,
            current, next_value, link, evaluator,
        )
        if isinstance(verified, Rejected):
            return verified
        predecessor = link.digest
        current = next_value
    if current != terminal_value or predecessor != terminal_digest:
        return Rejected(Failure.TERMINAL_MISMATCH)
    return VerifiedChain(current, predecessor)


def verified_prefix_anchor(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
    evaluators: Mapping[str, Evaluator],
    prefix_links: Sequence[Link],
) -> VerifiedPrefixAnchor | Rejected:
    if len(prefix_links) > len(route):
        return Rejected(Failure.PREFIX_MISMATCH)
    prepared = _identity_and_initial(epoch, entrypoint, route, route_input)
    if isinstance(prepared, Rejected):
        return prepared
    identity, current = prepared
    predecessor = initial_predecessor(epoch, entrypoint, identity)
    for phase, link in zip(route[:len(prefix_links)], prefix_links, strict=True):
        evaluator = evaluators.get(phase.phase_id)
        if evaluator is None:
            return Rejected(Failure.UNAVAILABLE)
        next_value = _safe_evaluate(
            phase, evaluator, current,
            epoch=epoch, entrypoint=entrypoint,
            route_identity=identity, route_input=route_input,
        )
        if isinstance(next_value, Rejected):
            return next_value
        verified = verify_link(
            epoch, entrypoint, identity, phase, len(route), predecessor,
            current, next_value, link, evaluator,
        )
        if isinstance(verified, Rejected):
            return Rejected(Failure.PREFIX_MISMATCH)
        predecessor = link.digest
        current = next_value
    receipt_body = _record({
        "route_hex": identity.hex(), "epoch_hex": epoch.hex(), "entrypoint": entrypoint,
        "predecessor_index": len(prefix_links) - 1, "boundary_type_id_hex": type_id(epoch, current.type_name).hex(),
        "boundary_value_id_hex": value_id(epoch, current).hex(), "predecessor_hex": predecessor.hex(),
        "verified_prefix_links": [link.digest.hex() for link in prefix_links],
    })
    return VerifiedPrefixAnchor(
        identity, epoch, entrypoint, len(prefix_links) - 1, current, predecessor,
        PrefixVerificationReceipt(_hash(b"AION-PREFIX-V2" + receipt_body)),
    )


def verify_section(
    epoch: bytes,
    entrypoint: str,
    route: Sequence[PhaseDeclaration],
    route_input: CanonicalRouteInput,
    evaluators: Mapping[str, Evaluator],
    prefix_links: Sequence[Link],
    section_links: Sequence[Link],
) -> SectionResult | Rejected:
    anchor = verified_prefix_anchor(epoch, entrypoint, route, route_input, evaluators, prefix_links)
    if isinstance(anchor, Rejected):
        return anchor
    start = len(prefix_links)
    if start + len(section_links) > len(route):
        return Rejected(Failure.CHAIN_LENGTH)
    current = anchor.boundary_value
    predecessor = anchor.predecessor_digest
    for phase, link in zip(route[start:start + len(section_links)], section_links, strict=True):
        evaluator = evaluators.get(phase.phase_id)
        if evaluator is None:
            return Rejected(Failure.UNAVAILABLE)
        next_value = _safe_evaluate(
            phase, evaluator, current,
            epoch=epoch, entrypoint=entrypoint,
            route_identity=anchor.route_identity, route_input=route_input,
        )
        if isinstance(next_value, Rejected):
            return next_value
        verified = verify_link(
            epoch, entrypoint, anchor.route_identity, phase, len(route), predecessor,
            current, next_value, link, evaluator,
        )
        if isinstance(verified, Rejected):
            return verified
        predecessor = link.digest
        current = next_value
    return SectionResult(current, predecessor, anchor)


def with_failure(evaluator: PhaseEvaluator, failure: Failure) -> PhaseEvaluator:
    if failure is Failure.TIMEOUT:
        return replace(evaluator, raise_timeout=True)
    if failure is Failure.UNAVAILABLE:
        return replace(evaluator, raise_unavailable=True)
    if failure is Failure.EXCEPTION:
        return replace(evaluator, raise_exception=True)
    return replace(evaluator, forced_failure=failure)
