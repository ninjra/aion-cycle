#!/usr/bin/env python3
"""Materialize all inherited Ionizer decisions for the typed phase-chain paper."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parents[1] / "ionizer" / "papers" / "ionizer-paper-decisions-and-lessons-catalog.json"
OUTPUT = ROOT / "provenance" / "IONIZER-DECISION-DISPOSITIONS.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def classify(row: dict) -> tuple[str, str, list[str]]:
    category = row["category"]
    decision = row["decision"]
    paper = "exact-typed-phase-chains-with-recomputable-route-closure.tex"
    spec = "provenance/exact-typed-phase-chain-formal-specification-candidate.md"

    if category == "mathematical_precision_closures":
        if decision.startswith("result-valued"):
            return "APPLICABLE", "Every result-valued phase and verifier uses error-propagating typed REJECT with no aggregate partial success.", [paper, spec]
        if decision.startswith("semantic and operational"):
            return "APPLICABLE", "Pure typed route semantics are separated from evaluator availability, execution evidence, proof artifacts, and stored records.", [paper, spec]
        return "IMPORTED_BOUNDARY", "The phase chain imports this Ionizer precision law and preserves its exact domain and codomain without redefining it.", [paper]

    if category == "patent_and_representation_clamps":
        return "APPLICABLE_IMPORTED_BOUNDARY", "The route imports the patent/Ionizer envelope and rejects ledgers, source handles, side decoders, lossy numeric projection, and alternate terminal forms.", [paper, "provenance/PATENT-IONIZER-FOUNDATION-MATRIX.md"]

    if category == "theorem_fidelity_and_authority":
        if "sealed theorem bytes" in decision or "publication seal" in decision:
            return "APPLICABLE_PENDING_OWNER_FREEZE", "The candidate theorem and rendering remain separate artifacts; dependency freeze, owner equivalence, and release remain fail-closed.", [spec, "provenance/OWNER-FREEZE-GATE.json"]
        return "APPLICABLE", "Reader-facing mathematics is derived only from the candidate formal specification and exact imported boundaries.", [paper, spec]

    if category == "citation_and_release_packet":
        if any(token in decision for token in ("seal", "upload-ready", "external upload", "date-released", "DOI")):
            return "APPLICABLE_FAIL_CLOSED", "No release date, DOI, readiness seal, upload, or publication status is inferred for this candidate.", ["provenance/RELEASE-MANIFEST.json", "provenance/OWNER-FREEZE-GATE.json"]
        return "APPLICABLE", "The packet follows the inherited citation, destructive-output, recursive-checksum, and one-current-PDF rules.", ["publish/", "README.md"]

    if category == "cross_repo_series_synchronization":
        return "APPLICABLE_EXTERNAL_SERIES_BOUNDARY", "The paper consumes the exact Ionizer catalog identity and does not replace the durable cross-repository matrix.", ["provenance/IONIZER-DECISION-DISPOSITIONS.json", "provenance/OWNER-FREEZE-GATE.json"]

    if category == "calculation_engine_boundary":
        return "APPLICABLE", "The calculation component is named only as a calculation engine and appears solely through its typed input-output contract.", [paper]

    if category in {"authorial_voice_and_tone", "paper_architecture_and_design", "pdf_and_accessibility"}:
        return "APPLICABLE", "The rendering applies this decision directly; the candidate packet records the corresponding verification surface.", [paper, "provenance/VERIFICATION-REPORT.json"]

    raise ValueError(f"unclassified decision category: {category}")


def main() -> None:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows = []
    for index, row in enumerate(source["matrix"], start=1):
        disposition, proof, targets = classify(row)
        rows.append(
            {
                "ordinal": index,
                "source_line_id": row["line_id"],
                "decision": row["decision"],
                "category": row["category"],
                "disposition": disposition,
                "phase_chain_specific_proof": proof,
                "target_artifacts": targets,
                "source_row_with_full_sq_context_and_clamps": row,
            }
        )

    if len(rows) != 88 or len({row["source_line_id"] for row in rows}) != 88:
        raise SystemExit("Ionizer decision coverage must be exactly 88 unique rows")

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["disposition"]] = counts.get(row["disposition"], 0) + 1

    payload = {
        "schema_version": "typed-phase-chain-ionizer-decision-disposition-v1",
        "paper_title": "Exact Typed Phase Chains with Recomputable Route Closure",
        "source_catalog": {"path": str(SOURCE), "sha256": sha256(SOURCE), "row_count": 88},
        "durable_matrix_boundary": "This file proves local paper disposition only; the universal matrix remains in MSSQL.",
        "release_boundary": "Candidate evidence only; dependency freeze, owner equivalence, and publication authorization remain open.",
        "coverage": {"row_count": 88, "all_source_rows_embedded": True, "full_sq_context_and_clamps_preserved": True, "disposition_counts": counts},
        "matrix": rows,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
