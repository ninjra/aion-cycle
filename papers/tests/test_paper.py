import hashlib
import importlib.util
import json
import re
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
TITLE = "Exact Typed Phase Chains with Recomputable Route Closure"
PDF_NAME = "exact-typed-phase-chains-with-recomputable-route-closure.pdf"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_facing_identity_voice_and_engine_boundary():
    tex = (ROOT / "exact-typed-phase-chains-with-recomputable-route-closure.tex").read_text()
    assert TITLE in tex
    for token in ("S N Justin Ram", "Mushku Nobleworks", "sram@mushku.com", "0009-0008-3593-2816"):
        assert token in tex
    assert "a calculation engine" in tex.lower()
    for forbidden in ("gravitas", "praetor", "sentinel", "the assistant", "the agent", "the human", "the user"):
        assert forbidden not in tex.lower()


def test_foundation_owner_and_dependency_gates_are_exact_and_fail_closed():
    matrix = (ROOT / "provenance" / "PATENT-IONIZER-FOUNDATION-MATRIX.md").read_text()
    for identity in (
        "e2975c587ae6299f86a84e4630c51a4de19b72abfaf4ec45c853f68775418240",
        "bf58f880e75aa4e62052bcefd59ce6c4fd44e80dcd941042f66e124e65de3efe",
    ):
        assert identity in matrix
    gate = json.loads((ROOT / "provenance" / "OWNER-FREEZE-GATE.json").read_text())
    assert gate["proof_passed"] is False
    assert gate["release_authorized"] is False
    assert gate["upload_ready"] is False
    joined = "\n".join(gate["observed_non_equivalence"])
    for token in ("source_record_id", "field_to_records", "fixed sint16", "not yet owner-frozen"):
        assert token in joined
    imports = json.loads((ROOT / "provenance" / "CROSS-PAPER-IMPORT-MATRIX.json").read_text())
    assert imports["whole_route_typecheck"] is True
    assert imports["two_operand_calculation_present"] is True
    assert imports["dual_wire_routes_complete"] is True
    assert imports["wire_owner_signatures_exact"] is True
    assert imports["origamold_codomain_separated"] is True
    assert imports["resolve_returns_dense_bytes"] is True
    assert imports["manifest_consumes_tensor_selector_target"] is True
    assert imports["proof_profile_coherent"] is True
    assert imports["route_v2_identity"] is True
    assert imports["dependency_freeze_complete"] is False
    assert all(check["verified"] for check in imports["verified_signature_checks"].values())
    for name in ("paper_ii", "paper_iii", "paper_iv"):
        assert digest(Path(imports["source_paths"][name])) == imports["dependencies"][name]["identity"]


def test_import_materializer_rejects_missing_exact_signature_fragments(tmp_path):
    module_path = ROOT / "tools" / "materialize_cross_paper_import_matrix.py"
    module_spec = importlib.util.spec_from_file_location("aion_import_matrix", module_path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    incomplete = tmp_path / "incomplete-companion.md"
    incomplete.write_text("unrelated bytes", encoding="utf-8")
    with pytest.raises(SystemExit, match="exact-signature mismatch"):
        module.require_fragments("synthetic", incomplete, ["required exact signature"])


def test_import_materializer_derives_wire_and_route_booleans_from_present_sources(tmp_path):
    module_path = ROOT / "tools" / "materialize_cross_paper_import_matrix.py"
    module_spec = importlib.util.spec_from_file_location("aion_import_matrix_derived", module_path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)

    internal, public = module.build_matrices()
    for field in (
        "whole_route_typecheck",
        "two_operand_calculation_present",
        "dual_wire_routes_complete",
        "wire_owner_signatures_exact",
        "proof_profile_coherent",
        "route_v2_identity",
    ):
        assert internal[field] is True
        assert public[field] == internal[field]

    altered_paper_v = tmp_path / "paper-v.md"
    altered_paper_v.write_text(
        module.SOURCES["paper_v"].read_text().replace(
            "W_in,A(b) = (b_in,rho,d_in).",
            "W_in,A(b) = widened-owner-tuple.",
        ),
        encoding="utf-8",
    )
    sources = dict(module.SOURCES)
    sources["paper_v"] = altered_paper_v
    with pytest.raises(SystemExit, match="paper_v exact-signature mismatch"):
        module.build_matrices(sources)


def test_all_88_decisions_are_dispositioned_with_full_context_and_clamps():
    data = json.loads((ROOT / "provenance" / "IONIZER-DECISION-DISPOSITIONS.json").read_text())
    assert data["source_catalog"]["sha256"] == "768f68a9c67dbf3a9be8ceaa251350dcd63ab59eb8ef4b6902a13b633613796d"
    assert len(data["matrix"]) == 88
    assert len({row["source_line_id"] for row in data["matrix"]}) == 88
    assert all(row["disposition"] for row in data["matrix"])
    assert all("authority_context_and_full_clamps" in row["source_row_with_full_sq_context_and_clamps"] for row in data["matrix"])


def test_candidate_spec_contains_corrected_exact_route_and_boundaries():
    spec = (ROOT / "provenance" / "exact-typed-phase-chain-formal-specification-candidate.md").read_text()
    for token in (
        "Calculate_A             : Tensor_A x Tensor_A",
        "Resolve_A               : Tensor_A x Selector_A",
        "Encode_A                = CanonicalEncoding_A",
        "Decode_A                = CanonicalDecode_A",
        "W_data,in,A(b_data)",
        "W_in,A(b) = (b_in,rho,d_in).",
        "W_out,A(rho,d_in,b_out) = (b_return,d_out).",
        "W_operation,in,A(b_operation)",
        "W_operation,out,A(rho_operation,d_operation,in,b_operation)",
        "Realize_A(D,Q;R_A)      = (W_q,K_q)",
        "Manifest_A,N(D,s,t)",
        "VerifyLink_A",
        "VerifyChain_A(C,D_operation,s,t",
        "AION-ROUTE-V2",
        "actual declared callable",
        "PDF pp. 8-9 / spec pp. 4-5",
        "No record stores `source_record_id`",
        "a calculation engine",
    ):
        assert token in spec
    assert "universal `sint16` semantic premise" in spec
    assert "b_operation,echo = b_operation byte for byte" in spec
    assert "SelectedHistory_A -> Window_A" not in spec
    assert "AtomicManifest_A      : Window_A" not in spec
    assert "Praetor" not in spec and "Gravitas" not in spec


def test_executable_candidate_and_exact_equality_boundary_are_present():
    model = (ROOT / "provenance" / "aion-exact-typed-phase-chain-theorem-candidate.py").read_text()
    assert "MAIN_ROUTE_TYPES" in model
    assert '"CALCULATE"' in model and "Operation" in model
    assert "AION-ROUTE-V2" in model and "AION-ROUTE-V3" not in model
    assert "input_type_id_hex" in model and "output_type_id_hex" in model
    assert "VerifiedChain" in model and "VerifiedLink" in model
    assert "boundary_values" not in model


def test_publish_packet_is_single_pdf_checksum_clean_and_not_released():
    manifest = json.loads((ROOT / "publish" / "provenance" / "RELEASE-MANIFEST.json").read_text())
    assert manifest["implementation_equivalence"] is False
    assert manifest["dependency_freeze_complete"] is False
    assert manifest["upload_ready"] is False
    assert manifest["publication_authorized"] is False
    assert manifest["doi"] is None and manifest["date_released"] is None
    pdfs = list((ROOT / "publish" / "papers").glob("*.pdf"))
    assert [p.name for p in pdfs] == [PDF_NAME]
    assert digest(pdfs[0]) == manifest["paper_pdf_sha256"]
    public_text = "\n".join(
        path.read_text(errors="ignore")
        for path in (ROOT / "publish").rglob("*")
        if path.is_file() and path.suffix.lower() != ".pdf"
    ).lower()
    for forbidden in ("gravitas", "praetor", "sentinel"):
        assert forbidden not in public_text
    assert re.search(r"/home/[A-Za-z0-9_.-]+", public_text) is None


def test_publish_checksums_verify():
    for line in (ROOT / "publish" / "SHA256SUMS").read_text().splitlines():
        expected, relative = line.split("  ", 1)
        assert digest(ROOT / "publish" / relative) == expected
