#!/usr/bin/env python3
"""Materialize Paper V companion signatures from present source bytes.

Every compatibility Boolean is derived from an exact source-fragment check or
from the executable fixed-route typecheck.  No public projection hard-codes a
successful compatibility result.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT.parents[1]
SOURCES = {
    "ionizer": PROJECTS_ROOT / "ionizer" / "papers" / "authority" / "ionizer-srft-v10-theorem.md",
    "paper_ii": PROJECTS_ROOT / "gravitas-wire" / "papers" / "provenance" / "wire-opaque-exact-transport-formal-specification-candidate.md",
    "paper_iii": PROJECTS_ROOT / "origamold" / "papers" / "exact-bounded-active-window-realization.tex",
    "paper_iv": PROJECTS_ROOT / "gravitas-energizer" / "papers" / "provenance" / "energizer-atomic-exact-manifestation-formal-specification-candidate.md",
    "paper_v": ROOT / "provenance" / "exact-typed-phase-chain-formal-specification-candidate.md",
    "paper_v_model": ROOT / "provenance" / "aion-exact-typed-phase-chain-theorem-candidate.py",
}

WIRE_OWNER_SIGNATURES = (
    "W_in,A(b) = (b_in,rho,d_in).",
    "W_out,A(rho,d_in,b_out) = (b_return,d_out).",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def fragment_present(path: Path, fragment: str) -> bool:
    return " ".join(fragment.split()) in normalized(path)


def require_fragments(name: str, path: Path, fragments: list[str]) -> dict:
    missing = [fragment for fragment in fragments if not fragment_present(path, fragment)]
    if missing:
        raise SystemExit(f"{name} exact-signature mismatch in {path}: missing {missing}")
    return {
        "source_sha256": digest(path),
        "required_fragments_sha256": [
            hashlib.sha256(" ".join(fragment.split()).encode("utf-8")).hexdigest()
            for fragment in fragments
        ],
        "verified": len(missing) == 0,
    }


def exact_shared_fragments(left: Path, right: Path, fragments: tuple[str, ...]) -> bool:
    return all(fragment_present(left, fragment) and fragment_present(right, fragment) for fragment in fragments)


def _load_model(path: Path):
    spec = importlib.util.spec_from_file_location("aion_paper_v_materialized_model", path)
    if not spec or not spec.loader:
        raise SystemExit(f"cannot load Paper V executable model: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def executable_route_checks(path: Path) -> dict[str, bool]:
    model = _load_model(path)
    plain = model.default_route()
    proof = model.default_route(b"proof-profile")
    plain_ids = [phase.phase_id for phase in plain]
    proof_ids = [phase.phase_id for phase in proof]
    fixed_ids = [row[0] for row in model.MAIN_ROUTE_TYPES]
    return {
        "whole_route_typecheck": bool(model.well_typed(plain) and model.fixed_route(plain, b"") and plain_ids == fixed_ids),
        "dual_wire_routes_complete": bool(
            plain_ids.index("WIRE_DATA_INGRESS") < plain_ids.index("WIRE_DATA_EGRESS")
            and plain_ids.index("WIRE_OPERATION_INGRESS") < plain_ids.index("WIRE_OPERATION_EGRESS")
        ),
        "two_operand_calculation_present": "Tensor*Tensor" in plain[plain_ids.index("CALCULATE")].input_type,
        "proof_profile_coherent": bool(
            "PROVE" not in plain_ids
            and "VERIFY" not in plain_ids
            and proof_ids[-3:] == ["PROVE", "VERIFY", "CLOSE"]
            and model.fixed_route(proof, b"proof-profile")
        ),
        "route_v2_identity": "AION-ROUTE-V3" not in path.read_text(encoding="utf-8")
        and "AION-ROUTE-V2" in path.read_text(encoding="utf-8"),
    }


def build_matrices(sources: Mapping[str, Path] = SOURCES) -> tuple[dict, dict]:
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise SystemExit(f"missing companion source: {missing}")

    checks = {
        "ionizer": require_fragments("ionizer", sources["ionizer"], [
            "CanonicalEncoding_A : CanonicalTensor_A -> U*",
            "CanonicalDecode_A : U* -> CanonicalTensor_A disjoint_union {REJECT}",
            "Calculate_A : CanonicalTensor_A x CanonicalTensor_A",
            "Resolve_A : CanonicalTensor_A x Selector_A",
        ]),
        "paper_ii": require_fragments("paper_ii", sources["paper_ii"], [
            *WIRE_OWNER_SIGNATURES,
            "An egress frame before a successful ingress, a second ingress",
        ]),
        "paper_iii": require_fragments("paper_iii", sources["paper_iii"], [
            "A demand is $Q=(q,b)$",
            "\\Realize_A(D,Q;R_A)",
            "\\in \\{(W_q,K_q)\\}\\sqcup\\{\\Reject\\}",
            "\\Read(W_q)=\\beta_{A,\\Lambda}(D|_q)",
        ]),
        "paper_iv": require_fragments("paper_iv", sources["paper_iv"], [
            "Manifest_A,N(D,s,t) =",
            "return PUBLISHED(t,len(C_s),H(C_s),B*,epoch(D),s).",
            "require ReadFinal_N(t) = C_s",
        ]),
        "paper_v": require_fragments("paper_v", sources["paper_v"], [
            *WIRE_OWNER_SIGNATURES,
            "Encode_A = CanonicalEncoding_A",
            "Decode_A = CanonicalDecode_A",
            "W_data,in,A(b_data) = W_in,A(b_data)",
            "W_operation,in,A(b_operation) = W_in,A(b_operation)",
            "W_operation,out,A(rho_operation,d_operation,in,b_operation) = W_out,A(rho_operation,d_operation,in,b_operation)",
            "b_operation,echo = b_operation byte for byte",
            "Calculate_A(D_data,D_operation)",
            "Resolve_A(D_result,s)",
            "Manifest_A,N(D_result,s,t)",
            '"AION-ROUTE-V2"',
            "The evaluator identity is derived from the actual declared callable",
        ]),
    }
    route_checks = executable_route_checks(sources["paper_v_model"])
    wire_owner_exact = exact_shared_fragments(sources["paper_ii"], sources["paper_v"], WIRE_OWNER_SIGNATURES)

    dependencies = {
        "ionizer": {
            "identity": digest(sources["ionizer"]),
            "owner_frozen": True,
            "imports": [
                "Phi_A: U* -> CanonicalTensor_A",
                "Encode_A = CanonicalEncoding_A: CanonicalTensor_A -> CanonicalBytes_A",
                "Decode_A = CanonicalDecode_A: B* -> CanonicalTensor_A disjoint-union REJECT",
                "Calculate_A: CanonicalTensor_A x CanonicalTensor_A -> CanonicalTensor_A disjoint-union REJECT",
                "Resolve_A: CanonicalTensor_A x Selector_A -> U* disjoint-union REJECT",
            ],
            "epoch_binding": "A",
            "bridge": "normative main-route semantic foundation",
        },
        "paper_ii": {
            "identity": digest(sources["paper_ii"]),
            "owner_frozen": False,
            "imports": [
                "W_in,A(b) = (b_in,rho,d_in)",
                "W_out,A(rho,d_in,b_out) = (b_return,d_out)",
                "Paper V instantiates two independent complete Wire routes without widening the owner tuples",
            ],
            "epoch_binding": "A",
            "bridge": "data and operation projections are exact identity at both canonical-byte crossings",
        },
        "paper_iii": {
            "identity": digest(sources["paper_iii"]),
            "owner_frozen": False,
            "imports": [
                "Q=(q,b); ConformingProfile_A(R_A)",
                "Realize_A(D,Q;R_A) -> (W_q,K_q) disjoint-union REJECT",
                "Read(W_q) = beta_A,Lambda(D|q)",
            ],
            "epoch_binding": "A",
            "bridge": "independent bounded tensor-realization section; never substituted for Resolve or Manifest",
        },
        "paper_iv": {
            "identity": digest(sources["paper_iv"]),
            "owner_frozen": False,
            "imports": [
                "Manifest_A,N(D,s,t) -> ManifestReceipt_A,N disjoint-union REJECT",
                "ManifestReceipt_A,N = PUBLISHED(t,len(C_s),H(C_s),B*,epoch(D),s)",
                "ReadFinal_N(t) = Resolve_A(D,s) on success",
            ],
            "epoch_binding": "A",
            "bridge": "direct manifestation from canonical D, selector, and target; no Window input",
        },
    }

    results = {
        "whole_route_typecheck": route_checks["whole_route_typecheck"] and checks["paper_v"]["verified"],
        "two_operand_calculation_present": route_checks["two_operand_calculation_present"] and checks["ionizer"]["verified"] and checks["paper_v"]["verified"],
        "dual_wire_routes_complete": route_checks["dual_wire_routes_complete"] and wire_owner_exact and checks["paper_v"]["verified"],
        "wire_owner_signatures_exact": wire_owner_exact,
        "origamold_codomain_separated": checks["paper_iii"]["verified"] and checks["paper_v"]["verified"],
        "resolve_returns_dense_bytes": checks["ionizer"]["verified"] and checks["paper_v"]["verified"],
        "manifest_consumes_tensor_selector_target": checks["paper_iv"]["verified"] and checks["paper_v"]["verified"],
        "proof_profile_coherent": route_checks["proof_profile_coherent"] and checks["paper_v"]["verified"],
        "route_v2_identity": route_checks["route_v2_identity"] and checks["paper_v"]["verified"],
    }
    if not all(check["verified"] for check in checks.values()) or not all(results.values()):
        raise SystemExit(f"cross-paper exact-signature verification incomplete: {results}")

    internal = {
        "schema_version": "aion-cross-paper-import-matrix-v3",
        "paper": "Exact Typed Phase Chains with Recomputable Route Closure",
        "dependencies": dependencies,
        "verified_signature_checks": checks,
        **results,
        "dependency_freeze_complete": all(item["owner_frozen"] for item in dependencies.values()),
        "source_paths": {name: str(path) for name, path in sources.items()},
        "boundary": "Exact signatures, shared owner fragments, executable route identity, and bridge laws are checked from present source. Hash equality alone is insufficient.",
    }
    public = {
        key: value for key, value in internal.items() if key != "source_paths"
    }
    public["schema_version"] = "aion-cross-paper-import-matrix-public-v3"
    return internal, public


def main() -> None:
    internal, public = build_matrices()
    for path, value in (
        (ROOT / "provenance" / "CROSS-PAPER-IMPORT-MATRIX.json", internal),
        (ROOT / "provenance" / "CROSS-PAPER-IMPORT-MATRIX-PUBLIC.json", public),
    ):
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
