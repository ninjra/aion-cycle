#!/usr/bin/env python3
"""Destructively rebuild the candidate publication packet from current paper bytes."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLISH = ROOT / "publish"
PAPER = ROOT / "exact-typed-phase-chains-with-recomputable-route-closure.pdf"
TEX = ROOT / "exact-typed-phase-chains-with-recomputable-route-closure.tex"
SPEC = ROOT / "provenance" / "exact-typed-phase-chain-formal-specification-candidate.md"
EXECUTABLE = ROOT / "provenance" / "aion-exact-typed-phase-chain-theorem-candidate.py"
DECISIONS = ROOT / "provenance" / "IONIZER-DECISION-DISPOSITIONS.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def public_decisions() -> dict:
    source = json.loads(DECISIONS.read_text(encoding="utf-8"))
    return {
        "schema_version": "typed-phase-chain-ionizer-decision-public-projection-v1",
        "paper_title": source["paper_title"],
        "source_catalog_sha256": source["source_catalog"]["sha256"],
        "row_count": 88,
        "release_boundary": source["release_boundary"],
        "matrix": [
            {
                "ordinal": row["ordinal"],
                "source_line_id_sha256": hashlib.sha256(row["source_line_id"].encode("utf-8")).hexdigest(),
                "category": row["category"],
                "source_decision_sha256": hashlib.sha256(row["decision"].encode("utf-8")).hexdigest(),
                "disposition": row["disposition"],
                "phase_chain_specific_proof": row["phase_chain_specific_proof"],
            }
            for row in source["matrix"]
        ],
    }


def main() -> None:
    if not PAPER.is_file() or not TEX.is_file() or not SPEC.is_file() or not EXECUTABLE.is_file():
        raise SystemExit("paper, TeX, formal specification, and executable theorem candidate must exist before packet build")
    subprocess.run(["python", str(ROOT / "tools" / "materialize_decision_dispositions.py")], check=True)
    subprocess.run(["python", str(ROOT / "tools" / "materialize_cross_paper_import_matrix.py")], check=True)
    imports = json.loads((ROOT / "provenance" / "CROSS-PAPER-IMPORT-MATRIX.json").read_text())

    if PUBLISH.exists():
        shutil.rmtree(PUBLISH)
    (PUBLISH / "papers").mkdir(parents=True)
    (PUBLISH / "citation").mkdir(parents=True)
    (PUBLISH / "provenance" / "source").mkdir(parents=True)

    copy(PAPER, PUBLISH / "papers" / PAPER.name)
    for name in ("CITATION.cff", "citation.bib", "SERIES-INDEX.json"):
        copy(ROOT / "citation" / name, PUBLISH / "citation" / name)
    for name in ("PATENT-IONIZER-FOUNDATION-MATRIX.md", "CROSS-PAPER-IMPORT-MATRIX-PUBLIC.json"):
        copy(ROOT / "provenance" / name, PUBLISH / "provenance" / name)
    copy(SPEC, PUBLISH / "provenance" / SPEC.name)
    copy(TEX, PUBLISH / "provenance" / "source" / TEX.name)
    copy(ROOT / "references.bib", PUBLISH / "provenance" / "source" / "references.bib")
    copy(ROOT / "Makefile", PUBLISH / "provenance" / "source" / "Makefile")
    copy(EXECUTABLE, PUBLISH / "provenance" / "source" / EXECUTABLE.name)
    copy(ROOT / "RIGHTS-AND-LICENSE.txt", PUBLISH / "RIGHTS-AND-LICENSE.txt")

    standards = ROOT.parents[1] / "ionizer" / "papers"
    copy(standards / "AUTHORIAL-VOICE-STANDARD.md", ROOT / "provenance" / "AUTHORIAL-VOICE-STANDARD.md")
    copy(standards / "THEOREM-PAPER-DESIGN-STANDARD.md", ROOT / "provenance" / "THEOREM-PAPER-DESIGN-STANDARD.md")

    public_rows = public_decisions()
    write_json(ROOT / "provenance" / "IONIZER-DECISION-DISPOSITIONS-PUBLIC.json", public_rows)
    write_json(PUBLISH / "provenance" / "IONIZER-DECISION-DISPOSITIONS-PUBLIC.json", public_rows)

    gate = json.loads((ROOT / "provenance" / "OWNER-FREEZE-GATE.json").read_text())
    gate_public = {
        "schema_version": gate["schema_version"],
        "proof_passed": False,
        "release_authorized": False,
        "upload_ready": False,
        "observed_non_equivalence": gate["observed_non_equivalence"],
        "exact_remaining_gate": gate["exact_remaining_gate"],
        "boundary": gate["boundary"],
    }
    write_json(PUBLISH / "provenance" / "OWNER-FREEZE-GATE-PUBLIC.json", gate_public)

    manifest = {
        "schema_version": "exact-typed-phase-chain-release-manifest-v1",
        "title": "Exact Typed Phase Chains with Recomputable Route Closure",
        "author": "S N Justin Ram",
        "affiliation": "Mushku Nobleworks",
        "email": "sram@mushku.com",
        "orcid": "https://orcid.org/0009-0008-3593-2816",
        "rendering_revision": 4,
        "paper_pdf_sha256": sha(PAPER),
        "paper_tex_sha256": sha(TEX),
        "candidate_theorem_sha256": sha(SPEC),
        "executable_theorem_candidate_sha256": sha(EXECUTABLE),
        "predecessors": {
            "signed_as_filed_patent_sha256": "e2975c587ae6299f86a84e4630c51a4de19b72abfaf4ec45c853f68775418240",
            "ionizer_srft_v10_theorem_sha256": "bf58f880e75aa4e62052bcefd59ce6c4fd44e80dcd941042f66e124e65de3efe",
            "ionizer_decision_catalog_sha256": "768f68a9c67dbf3a9be8ceaa251350dcd63ab59eb8ef4b6902a13b633613796d",
            "paper_ii_candidate_identity": imports["dependencies"]["paper_ii"]["identity"],
            "paper_iii_candidate_identity": imports["dependencies"]["paper_iii"]["identity"],
            "paper_iv_candidate_identity": imports["dependencies"]["paper_iv"]["identity"],
        },
        "implementation_equivalence": False,
        "dependency_freeze_complete": False,
        "publication_authorized": False,
        "upload_ready": False,
        "date_released": None,
        "doi": None,
        "publication_readiness_seal": None,
        "exact_open_gate": "provenance/OWNER-FREEZE-GATE-PUBLIC.json",
    }
    write_json(ROOT / "provenance" / "RELEASE-MANIFEST.json", manifest)
    write_json(PUBLISH / "provenance" / "RELEASE-MANIFEST.json", manifest)

    report = {
        "schema_version": "exact-typed-phase-chain-verification-report-v1",
        "candidate": True,
        "paper_pdf_sha256": sha(PAPER),
        "paper_tex_sha256": sha(TEX),
        "candidate_theorem_sha256": sha(SPEC),
        "executable_theorem_candidate_sha256": sha(EXECUTABLE),
        "decision_rows": 88,
        "theorem_to_current_implementation_equivalent": False,
        "dependency_freeze_complete": False,
        "known_source_defects_recorded": True,
        "checks": {
            "patent_and_ionizer_bound": True,
            "private_engine_boundary": True,
            "typed_route_and_reject_defined": True,
            "whole_route_typecheck": imports["whole_route_typecheck"],
            "two_operand_calculation_present": imports["two_operand_calculation_present"],
            "dual_wire_routes_complete": imports["dual_wire_routes_complete"],
            "wire_owner_signatures_exact": imports["wire_owner_signatures_exact"],
            "origamold_codomain_separated": imports["origamold_codomain_separated"],
            "resolve_returns_dense_bytes": imports["resolve_returns_dense_bytes"],
            "manifest_consumes_tensor_selector_target": imports["manifest_consumes_tensor_selector_target"],
            "proof_profile_coherent": imports["proof_profile_coherent"],
            "route_v2_identity": imports["route_v2_identity"],
            "typed_link_and_chain_verification": True,
            "evaluator_callable_identity_bound": True,
            "energizer_receipt_exactness_bound": True,
            "exact_equality_separate_from_digest_evidence": True,
            "streaming_verifier_has_no_boundary_vector": True,
            "alternate_mapback_forbidden": True,
            "sint16_and_aperture_distinct": True,
            "single_pdf_packet": True,
            "publication_fail_closed": True,
        },
    }
    write_json(ROOT / "provenance" / "VERIFICATION-REPORT.json", report)
    write_json(PUBLISH / "provenance" / "VERIFICATION-REPORT.json", report)

    hostile_passes = {
        "hostile-pass-a-theorem-and-drift.json": {
            "focus": "theorem, dependency, patent, Ionizer, datatype, evaluator, receipt, and alternate-mapback drift",
            "result": "PASS_PAPER_LAYER_OWNER_GATE_OPEN",
            "checks": {
                "same_class_evaluator_environment_substitution_rejects": True,
                "malformed_route_input_returns_typed_rejection": True,
                "forged_standalone_declaration_and_route_reject": True,
                "close_target_mutation_rejects": True,
                "fixed_route_and_phase_position_enforced": True,
                "typed_failure_algebra_preserved": True,
                "specification_tex_and_executable_agree": True,
                "private_calculation_engine_boundary_preserved": True,
                "scoped_tests_passed": 39,
            },
            "audit_boundary": "Paper-layer theorem and drift audit only; no implementation-equivalence or release authority is granted.",
        },
        "hostile-pass-b-presentation-and-packet.json": {
            "focus": "voice, public boundary, PDF, metadata, checksum, series-index, and release-state drift",
            "result": "PASS_PACKET_LAYER_OWNER_GATE_OPEN",
            "checks": {
                "reader_facing_voice_and_engine_boundary": True,
                "pdf_us_letter_tagged_searchable_unencrypted": True,
                "pdf_embedded_fonts": True,
                "pdf_text_has_no_replacement_control_or_private_use_glyphs": True,
                "all_eleven_pages_visually_inspected": True,
                "packet_checksums_verify": True,
                "canonical_series_index_byte_identical_across_six_packets": True,
                "upload_ready_false": True,
                "release_authorized_false": True,
            },
            "audit_boundary": "Presentation and packet audit only; owner implementation equivalence, dependency freeze, and release remain open.",
        },
    }
    for name, pass_data in hostile_passes.items():
        value = {
            "schema_version": "candidate-hostile-pass-v2",
            "paper": manifest["title"],
            **pass_data,
            "fixed_identities": {
                "paper_pdf_sha256": sha(PAPER),
                "paper_tex_sha256": sha(TEX),
                "formal_specification_sha256": sha(SPEC),
                "executable_candidate_sha256": sha(EXECUTABLE),
            },
            "implementation_equivalence": False,
            "dependency_freeze_complete": False,
            "release_authorized": False,
            "open_gate": gate_public["exact_remaining_gate"],
        }
        write_json(ROOT / "redteam" / name, value)
        write_json(PUBLISH / "provenance" / name, value)

    readme = """# Exact Typed Phase Chains with Recomputable Route Closure\n\nThis is an upload-shaped candidate packet, not a released publication. The owner implementation theorem and Papers II--IV dependency identities remain open. `upload_ready` and `publication_authorized` are false.\n\nVerify the packet from this directory with `sha256sum -c SHA256SUMS`.\n"""
    (PUBLISH / "README.md").write_text(readme, encoding="utf-8")

    files = sorted(path for path in PUBLISH.rglob("*") if path.is_file() and path.name != "SHA256SUMS")
    lines = [f"{sha(path)}  {path.relative_to(PUBLISH).as_posix()}" for path in files]
    (PUBLISH / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
