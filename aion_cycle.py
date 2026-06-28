#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_TRANSCRIPT_ROOT = "9f6071ca3e5b314fd295cb7a4461a38ef14573a4395352e288f84304f5aa8756"
DOMAIN = b"AION-CYCLE-V1|"
PTAU = "powersOfTau28_hez_final_18.ptau"
PTAU_SHA256 = "e970efa7774da80101e0ac336d083ef3339855c98112539338d706b2b89ac694"
CIRCOM_SHA256 = "85342c7ff332d948df7c0c50ecf201e6129349aef550ce873f3c811b79fe53a3"
EXPECTED_TOOL_VERSIONS = {"circom": "circom compiler 2.2.3", "snarkjs": "snarkjs@0.7.6"}
PUBLIC_BEACON_HEX = "936fc578d78c5a8fc92863f1e4393e35fa8318ce4e65fd1311b40e68dc75f6ea"
PUBLIC_BEACON_ITERATIONS = "10"
ROOT = Path(__file__).resolve().parent
BUNDLE_DIR = ROOT / "proofs" / "v1"
LENS = {"query": 30, "corpus0": 42, "corpus1": 33, "corpus2": 24, "emitted": 42}

SCHEMA_TRANSITION_EMISSION = "aion-transition-emission-v1"
SCHEMA_FINAL_EMISSION = "aion-cycle-final-emission-v1"
PUBLIC_ROUTE_ID = "source->encode->carry->compare->carry-back->map-back->write->prove->verify->close"
EMISSIONS_DIR = BUNDLE_DIR / "emissions"
PHASE_RECEIPTS_DIR = BUNDLE_DIR / "receipts"
TRANSITION_SPECS = [
    (0, "source", "source_fixture", "source_bytes"),
    (1, "encode", "source_bytes", "bounded_fields"),
    (2, "carry", "bounded_fields", "opaque_field_carry"),
    (3, "compare", "opaque_field_carry", "selection"),
    (4, "carry-back", "selection", "selected_field_hash"),
    (5, "map-back", "selected_field_hash", "selected_source_bytes"),
    (6, "write", "selected_source_bytes", "emitted_bytes"),
    (7, "prove", "emitted_bytes", "proof_artifacts"),
    (8, "verify", "proof_artifacts", "cycle_statement"),
]

PHASE_RECEIPT_ORDER = [
    "source",
    "encode",
    "carry",
    "compare",
    "carry_back",
    "map_back",
    "write",
    "prove",
    "verify",
    "cycle",
]


class AionFailure(RuntimeError):
    """Controlled public-safe failure with a stable reason code."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def fail(reason: str) -> None:
    raise AionFailure(reason)


_EXPLAIN_CHECKS: list[str] = []


def checkpoint(label: str) -> None:
    """Record a human-readable verification step for explain mode."""
    _EXPLAIN_CHECKS.append(label)


def failure_reason(exc: BaseException) -> str:
    if isinstance(exc, AionFailure):
        return exc.reason
    text = str(exc).strip()
    if text and all(ch.isalnum() or ch in "_:-." for ch in text):
        return text
    return f"internal_error:{type(exc).__name__}"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def file_sha(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def public_path_id(path_text: str) -> dict[str, str]:
    path = Path(path_text)
    name = path.name or path_text
    return {
        "name": name,
        "path_kind": "local",
        "path_sha256": sha256_hex(str(path).encode("utf-8")),
    }


def normalize_cmd(cmd: list[str]) -> list[str]:
    out: list[str] = []
    for item in cmd:
        text = str(item)
        try:
            path = Path(text)
            if path.is_absolute():
                if path.is_relative_to(ROOT):
                    out.append(str(path.relative_to(ROOT)))
                else:
                    out.append(path.name)
                continue
        except Exception:
            pass
        out.append(text)
    return out


def resolve_tool(tool: str) -> str | None:
    if tool == "snarkjs":
        local = ROOT / "node_modules" / ".bin" / "snarkjs"
        if local.exists():
            return str(local)
    return shutil.which(tool)


def tool_binary_sha(path_text: str) -> str:
    path = Path(path_text)
    if path.is_file():
        return file_sha(path)
    try:
        resolved = Path(path_text).resolve()
        if resolved.is_file():
            return file_sha(resolved)
    except Exception:
        pass
    return ""


def receipt(kind: str, payload: dict[str, Any], children: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    failed = list(payload.get("failed_checks") or [])
    child_hashes = [c["receipt_hash"] for c in children or []]
    if any(c.get("proof_passed") is not True for c in children or []):
        failed.append("child_failed")
    body = {"schema_version": f"aion-{kind}-receipt-v1", **payload, "child_receipt_hashes": child_hashes}
    body["failed_checks"] = failed
    body["proof_passed"] = not failed
    body["receipt_hash"] = sha256_hex(canonical_bytes(body))
    return body



def identity(label: str, data: bytes) -> dict[str, Any]:
    return {"label": label, "sha256": sha256_hex(data), "byte_count": len(data)}


def json_identity(label: str, value: Any) -> dict[str, Any]:
    data = canonical_bytes(value)
    return identity(label, data)


def emission_hash(emission: dict[str, Any]) -> str:
    body = dict(emission)
    body.pop("claimed_emission_hash", None)
    body.pop("emission_hash", None)
    return sha256_hex(canonical_bytes(body))


def final_emission_hash(final: dict[str, Any]) -> str:
    body = dict(final)
    body.pop("final_emission_hash", None)
    return sha256_hex(canonical_bytes(body))


def field_view(query: bytes, corpus: list[bytes]) -> dict[str, Any]:
    return {
        "query_histogram": dict(sorted(Counter(query).items())),
        "corpus_histograms": [dict(sorted(Counter(c).items())) for c in corpus],
    }


def score_view(query: bytes, corpus: list[bytes]) -> dict[str, Any]:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    return {"scores": scores, "winner": select_winner(query, corpus)}


def source_record_id(index: int, data: bytes) -> str:
    return f"corpus{index}:{sha256_hex(data)[:16]}"


def field_hash(data: bytes) -> str:
    return sha256_hex(data)


def phase_source(fixture: dict[str, Any]) -> dict[str, Any]:
    query = fixture["query"].encode("utf-8", "strict")
    corpus = [c.encode("utf-8", "strict") for c in fixture["corpus"]]
    return {"query": query, "corpus": corpus, "identity": json_identity("source_fixture", fixture)}


def phase_encode(query: bytes, corpus: list[bytes]) -> dict[str, Any]:
    fields = field_view(query, corpus)
    ledger = {
        "records": {source_record_id(i, data): data.hex() for i, data in enumerate(corpus)},
        "field_to_records": {},
    }
    for i, data in enumerate(corpus):
        ledger["field_to_records"].setdefault(field_hash(data), []).append(source_record_id(i, data))
    return {"fields": fields, "ledger": ledger, "identity": json_identity("bounded_fields", {"fields": fields, "ledger": ledger})}


def phase_carry(encoded: dict[str, Any]) -> dict[str, Any]:
    carried = {"fields": encoded["fields"], "ledger": encoded["ledger"], "carry_kind": "opaque_reference_carry"}
    return {"carried": carried, "identity": json_identity("opaque_field_carry", carried)}


def phase_compare(query: bytes, corpus: list[bytes], carried: dict[str, Any]) -> dict[str, Any]:
    scores = score_view(query, corpus)
    winner = int(scores["winner"])
    selected = {
        "scores": scores["scores"],
        "winner": winner,
        "selected_record_id": source_record_id(winner, corpus[winner]),
        "selected_field_hash": field_hash(corpus[winner]),
    }
    return {"selection": selected, "identity": json_identity("selection", selected)}


def phase_carry_back(selection: dict[str, Any]) -> dict[str, Any]:
    selected = {"selected_field_hash": selection["selected_field_hash"], "winner": selection["winner"]}
    return {"selected": selected, "identity": json_identity("selected_field_hash", selected)}


def phase_map_back(selected: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    records = list(ledger.get("field_to_records", {}).get(selected["selected_field_hash"], []))
    if len(records) != 1:
        fail("mapback_ambiguous_or_missing_field_hash")
    record_id = records[0]
    material_hex = ledger.get("records", {}).get(record_id)
    if not isinstance(material_hex, str):
        fail("mapback_record_missing")
    data = bytes.fromhex(material_hex)
    mapped = {"source_record_id": record_id, "source_bytes_sha256": sha256_hex(data), "byte_count": len(data)}
    return {"mapped": mapped, "bytes": data, "identity": json_identity("selected_source_bytes", mapped)}


def phase_write(mapped_bytes: bytes) -> dict[str, Any]:
    return {"emitted": bytes(mapped_bytes), "identity": identity("emitted_bytes", bytes(mapped_bytes))}


def run_host_route(query: bytes, corpus: list[bytes]) -> dict[str, Any]:
    fixture = {"query": query.decode("utf-8", "strict"), "corpus": [c.decode("utf-8", "strict") for c in corpus]}
    src = phase_source(fixture)
    enc = phase_encode(query, corpus)
    car = phase_carry(enc)
    comp = phase_compare(query, corpus, car["carried"])
    back = phase_carry_back(comp["selection"])
    mapped = phase_map_back(back["selected"], enc["ledger"])
    written = phase_write(mapped["bytes"])
    transcript_root = sha256_hex(DOMAIN + query + corpus[0] + corpus[1] + corpus[2] + written["emitted"])
    return {
        "source": src,
        "encode": enc,
        "carry": car,
        "compare": comp,
        "carry_back": back,
        "map_back": mapped,
        "write": written,
        "emitted": written["emitted"],
        "transcript_root": transcript_root,
    }


def public_material_identities(statement_data: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    fx_path = ROOT / "fixtures" / "canonical.json"
    fx = json.loads(fx_path.read_text(encoding="utf-8"))
    q = fx["query"].encode("utf-8", "strict")
    corpus = [c.encode("utf-8", "strict") for c in fx["corpus"]]
    host = run_host_route(q, corpus)
    emitted, transcript_root = host["emitted"], host["transcript_root"]
    fields = field_view(q, corpus)
    scores = score_view(q, corpus)
    selected_hash = host["carry_back"]["selected"]["selected_field_hash"]
    statement_data = statement_data or json.loads((ROOT / "aion.statement.json").read_text(encoding="utf-8"))
    source = json_identity("canonical_fixture", fx)
    source_material = json_identity("source_material", {"query": fx["query"], "corpus": fx["corpus"]})
    field = host["encode"]["identity"]
    carried = host["carry"]["identity"]
    selection = host["compare"]["identity"]
    selected = host["carry_back"]["identity"]
    selected_bytes = host["map_back"]["identity"]
    emitted_id = host["write"]["identity"]
    proof_artifacts = identity("proof_artifacts", str(statement_data.get("proof_root", "")).encode("utf-8"))
    statement_id = identity("cycle_statement", canonical_bytes(statement_data))
    return {
        "source_root": source,
        "source": source,
        "source_material": source_material,
        "field": field,
        "carried": carried,
        "selection": selection,
        "selected": selected,
        "selected_bytes": selected_bytes,
        "emitted": emitted_id,
        "proof_artifacts": proof_artifacts,
        "statement": statement_id,
        "transcript_root": identity("transcript_root", transcript_root.encode("utf-8")),
    }


def build_transition_emissions(statement_data: dict[str, Any]) -> list[dict[str, Any]]:
    ids = public_material_identities(statement_data)
    pairs = [
        (ids["source"], ids["source_material"]),
        (ids["source_material"], ids["field"]),
        (ids["field"], ids["carried"]),
        (ids["carried"], ids["selection"]),
        (ids["selection"], ids["selected"]),
        (ids["selected"], ids["selected_bytes"]),
        (ids["selected_bytes"], ids["emitted"]),
        (ids["emitted"], ids["proof_artifacts"]),
        (ids["proof_artifacts"], ids["statement"]),
    ]
    emissions: list[dict[str, Any]] = []
    previous = ""
    prior_hashes: list[str] = []
    for (index, transition_id, domain_from, domain_to), (inp, out) in zip(TRANSITION_SPECS, pairs):
        emission = {
            "schema_version": SCHEMA_TRANSITION_EMISSION,
            "route_id": PUBLIC_ROUTE_ID,
            "transition_id": transition_id,
            "transition_index": index,
            "chain_length": len(TRANSITION_SPECS),
            "domain_from": domain_from,
            "domain_to": domain_to,
            "source_root": ids["source_root"],
            "source_lineage_hashes": list(prior_hashes),
            "previous_emission_hash": previous,
            "input_identity": inp,
            "output_identity": out,
            "child_emission_hashes": [],
            "next_expected_transition": TRANSITION_SPECS[index + 1][1] if index + 1 < len(TRANSITION_SPECS) else "final-cycle",
            "claimed_passed": True,
        }
        h = emission_hash(emission)
        emission["claimed_emission_hash"] = h
        emissions.append(emission)
        previous = h
        prior_hashes.append(h)
    return emissions


def build_final_emission(statement_data: dict[str, Any], transition_emissions: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = [e["claimed_emission_hash"] for e in transition_emissions]
    ids = public_material_identities(statement_data)
    final = {
        "schema_version": SCHEMA_FINAL_EMISSION,
        "route_id": PUBLIC_ROUTE_ID,
        "source_root": ids["source_root"],
        "transition_emission_hashes": hashes,
        "chain_tip": hashes[-1] if hashes else "",
        "transcript_root": statement_data.get("transcript_root"),
        "proof_root": statement_data.get("proof_root"),
        "cycle_root": statement_data.get("cycle_root"),
        "output_sha256": ids["emitted"]["sha256"],
        "output_byte_count": ids["emitted"]["byte_count"],
        "computed_passed": True,
        "failed_checks": [],
    }
    final["final_emission_hash"] = final_emission_hash(final)
    return final


def build_phase_receipts(statement_data: dict[str, Any]) -> list[dict[str, Any]]:
    ids = public_material_identities(statement_data)
    phase_pairs = [
        ("source", ids["source_root"], ids["source_material"]),
        ("encode", ids["source_material"], ids["field"]),
        ("carry", ids["field"], ids["carried"]),
        ("compare", ids["carried"], ids["selection"]),
        ("carry_back", ids["selection"], ids["selected"]),
        ("map_back", ids["selected"], ids["selected_bytes"]),
        ("write", ids["selected_bytes"], ids["emitted"]),
        ("prove", ids["emitted"], ids["proof_artifacts"]),
        ("verify", ids["proof_artifacts"], ids["statement"]),
    ]
    receipts: list[dict[str, Any]] = []
    for index, (phase, inp, out) in enumerate(phase_pairs):
        children = receipts[-1:] if receipts else []
        receipts.append(receipt("phase", {
            "phase": phase,
            "phase_index": index,
            "route_id": PUBLIC_ROUTE_ID,
            "input_identity": inp,
            "output_identity": out,
        }, children))
    cycle_receipt = receipt("cycle", {
        "phase": "cycle",
        "route_id": PUBLIC_ROUTE_ID,
        "phase_receipt_hashes": [r["receipt_hash"] for r in receipts],
        "transcript_root": statement_data.get("transcript_root"),
        "proof_root": statement_data.get("proof_root"),
        "cycle_root": statement_data.get("cycle_root"),
    }, receipts)
    receipts.append(cycle_receipt)
    return receipts


def write_phase_receipts(statement_data: dict[str, Any]) -> None:
    if PHASE_RECEIPTS_DIR.exists():
        shutil.rmtree(PHASE_RECEIPTS_DIR)
    PHASE_RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for rec in build_phase_receipts(statement_data):
        phase = str(rec["phase"])
        index = PHASE_RECEIPT_ORDER.index(phase) if phase in PHASE_RECEIPT_ORDER else 99
        (PHASE_RECEIPTS_DIR / f"{index:02d}-{phase}.receipt.json").write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_phase_receipts() -> list[dict[str, Any]]:
    if not PHASE_RECEIPTS_DIR.is_dir():
        fail("phase_receipts_missing")
    receipts = [load_verified_receipt(path) for path in sorted(PHASE_RECEIPTS_DIR.glob("[0-9][0-9]-*.receipt.json"))]
    if [r.get("phase") for r in receipts] != PHASE_RECEIPT_ORDER:
        fail("phase_receipt_order_mismatch")
    return receipts


def verify_phase_receipts(statement_data: dict[str, Any]) -> None:
    actual = load_phase_receipts()
    expected = build_phase_receipts(statement_data)
    if len(actual) != len(expected):
        fail("phase_receipt_count_mismatch")
    for index, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            fail(f"phase_receipt_{index}_mismatch")


def write_emission_chain(statement_data: dict[str, Any]) -> None:
    if EMISSIONS_DIR.exists():
        shutil.rmtree(EMISSIONS_DIR)
    EMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    transitions = build_transition_emissions(statement_data)
    for emission in transitions:
        name = f"{int(emission['transition_index']):02d}-{emission['transition_id']}.emission.json"
        (EMISSIONS_DIR / name).write_text(json.dumps(emission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    final = build_final_emission(statement_data, transitions)
    (EMISSIONS_DIR / "final-cycle.emission.json").write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_emission_chain() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not EMISSIONS_DIR.is_dir():
        fail("emission_chain_missing")
    transitions = []
    for path in sorted(EMISSIONS_DIR.glob("[0-9][0-9]-*.emission.json")):
        transitions.append(json.loads(path.read_text(encoding="utf-8")))
    final_path = EMISSIONS_DIR / "final-cycle.emission.json"
    if not final_path.is_file():
        fail("final_emission_missing")
    return transitions, json.loads(final_path.read_text(encoding="utf-8"))


def verify_cache_material(cache: dict[str, Any], expected_sha256: str) -> bool:
    # Cache flags are intentionally ignored. The bytes are authority only after
    # present-tense recomputation of their identity.
    encoded = cache.get("material_hex")
    if not isinstance(encoded, str):
        fail("cache_material_missing")
    data = bytes.fromhex(encoded)
    if sha256_hex(data) != expected_sha256:
        fail("cache_material_hash_mismatch")
    return True


def verify_emission_lineage(statement_data: dict[str, Any], transitions: list[dict[str, Any]], final: dict[str, Any]) -> None:
    expected_transitions = build_transition_emissions(statement_data)
    if len(transitions) != len(expected_transitions):
        fail("emission_count_mismatch")
    previous = ""
    computed_hashes: list[str] = []
    source_root = public_material_identities(statement_data)["source_root"]
    for idx, (actual, expected) in enumerate(zip(transitions, expected_transitions)):
        for key in ("schema_version", "route_id", "transition_id", "transition_index", "chain_length", "domain_from", "domain_to", "input_identity", "output_identity", "source_root", "previous_emission_hash", "source_lineage_hashes"):
            if actual.get(key) != expected.get(key):
                fail(f"emission_{idx}_{key}_mismatch")
        if actual.get("source_root") != source_root:
            fail("emission_source_root_mismatch")
        if actual.get("previous_emission_hash") != previous:
            fail("emission_previous_hash_mismatch")
        if actual.get("source_lineage_hashes") != computed_hashes:
            fail("emission_lineage_hashes_mismatch")
        computed = emission_hash(actual)
        if actual.get("claimed_emission_hash") != computed:
            fail("emission_hash_mismatch")
        if actual.get("claimed_passed") is not True:
            fail("emission_claimed_pass_mismatch")
        previous = computed
        computed_hashes.append(computed)
    expected_final = build_final_emission(statement_data, expected_transitions)
    for key in ("schema_version", "route_id", "source_root", "transition_emission_hashes", "chain_tip", "transcript_root", "proof_root", "cycle_root", "output_sha256", "output_byte_count"):
        if final.get(key) != expected_final.get(key):
            fail(f"final_emission_{key}_mismatch")
    if final.get("transition_emission_hashes") != computed_hashes:
        fail("final_emission_child_hash_mismatch")
    if final.get("chain_tip") != (computed_hashes[-1] if computed_hashes else ""):
        fail("final_emission_chain_tip_mismatch")
    if final.get("computed_passed") is not True or final.get("failed_checks") != []:
        fail("final_emission_claim_mismatch")
    if final.get("final_emission_hash") != final_emission_hash(final):
        fail("final_emission_hash_mismatch")


def verify_section_reentry(statement_data: dict[str, Any], section: dict[str, Any], transitions: list[dict[str, Any]], final: dict[str, Any]) -> None:
    verify_emission_lineage(statement_data, transitions, final)
    h = section.get("claimed_emission_hash")
    if h not in final.get("transition_emission_hashes", []):
        fail("section_not_in_final_emission")
    index = final["transition_emission_hashes"].index(h)
    if transitions[index].get("claimed_emission_hash") != h:
        fail("section_position_mismatch")
    if emission_hash(section) != h:
        fail("section_hash_mismatch")


def bits_le(value: int, width: int) -> list[str]:
    return [str((int(value) >> i) & 1) for i in range(width)]


def inv_or_zero(diff: int) -> str:
    p = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    v = int(diff) % p
    return "0" if v == 0 else str(pow(v, -1, p))


def select_winner(query: bytes, corpus: list[bytes]) -> int:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    if scores.count(max(scores)) != 1:
        fail("ambiguous_or_no_winner")
    return max(range(len(scores)), key=lambda i: scores[i])


def build_input(query: bytes, corpus: list[bytes], emitted: bytes, digest_hex: str) -> dict[str, Any]:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    if scores[0] <= scores[1] or scores[0] <= scores[2]:
        fail("winner_not_corpus0")
    digest = bytes.fromhex(digest_hex)
    return {
        "query": [str(x) for x in query],
        "corpus0": [str(x) for x in corpus[0]],
        "corpus1": [str(x) for x in corpus[1]],
        "corpus2": [str(x) for x in corpus[2]],
        "emitted": [str(x) for x in emitted],
        "query_bits": [bits_le(x, 8) for x in query],
        "corpus0_bits": [bits_le(x, 8) for x in corpus[0]],
        "corpus1_bits": [bits_le(x, 8) for x in corpus[1]],
        "corpus2_bits": [bits_le(x, 8) for x in corpus[2]],
        "emitted_bits": [bits_le(x, 8) for x in emitted],
        "eq0_inv": [inv_or_zero(a - d) for a in query for d in corpus[0]],
        "eq1_inv": [inv_or_zero(a - d) for a in query for d in corpus[1]],
        "eq2_inv": [inv_or_zero(a - d) for a in query for d in corpus[2]],
        "ge01_bits": bits_le(scores[0] - scores[1] - 1, 16),
        "ge02_bits": bits_le(scores[0] - scores[2] - 1, 16),
        "expected_digest_bits": [str((digest[k // 8] >> (7 - (k % 8))) & 1) for k in range(256)],
    }


def run(cmd: list[str], cwd: Path, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, check=False)


def toolchain_receipt() -> dict[str, Any]:
    data: dict[str, Any] = {}
    for tool in ("node", "circom", "snarkjs"):
        path = resolve_tool(tool)
        if not path:
            fail(f"missing_{tool}")
        cp = run([path, "--version"], ROOT, 30)
        version = (cp.stdout + cp.stderr).strip()[:500]
        version_line = version.splitlines()[0] if version else ""
        if tool in EXPECTED_TOOL_VERSIONS and version_line != EXPECTED_TOOL_VERSIONS[tool]:
            fail(f"{tool}_version_mismatch")
        item = {**public_path_id(path), "version": version, "binary_sha256": tool_binary_sha(path)}
        if tool == "circom":
            item["expected_sha256"] = CIRCOM_SHA256
            if item["binary_sha256"] != CIRCOM_SHA256:
                fail("circom_hash_mismatch")
        data[tool] = item
    ptau = ROOT / PTAU
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    if not ptau.exists() or not circomlib.is_dir():
        fail("missing_ptau_or_circomlib")
    if file_sha(ptau) != PTAU_SHA256:
        fail("ptau_hash_mismatch")
    return receipt("toolchain", {
        "toolchain": data,
        "ptau": {"path": PTAU, "sha256": file_sha(ptau), "expected_sha256": PTAU_SHA256},
        "package_lock_sha256": file_sha(ROOT / "package-lock.json"),
    })


def checked(cmd: list[str], cwd: Path, commands: list[dict[str, Any]], timeout: int = 900) -> subprocess.CompletedProcess[str]:
    cp = run(cmd, cwd, timeout)
    commands.append({"cmd": normalize_cmd(cmd), "returncode": cp.returncode, "stdout_sha256": sha256_hex(cp.stdout.encode()), "stderr_sha256": sha256_hex(cp.stderr.encode())})
    if cp.returncode != 0:
        fail("command_failed")
    return cp


def prove(circuit_input: dict[str, Any]) -> dict[str, Any]:
    tc = toolchain_receipt()
    if BUNDLE_DIR.exists():
        shutil.rmtree(BUNDLE_DIR)
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    work = BUNDLE_DIR
    (work / "input.json").write_text(json.dumps(circuit_input, sort_keys=True), encoding="utf-8")
    commands: list[dict[str, Any]] = []
    circom = shutil.which("circom")
    snarkjs = resolve_tool("snarkjs")
    circomlib = ROOT / "node_modules" / "circomlib" / "circuits"
    ptau = ROOT / PTAU
    checked([circom, str(ROOT / "aion.circom"), "--r1cs", "--wasm", "--sym", "-l", str(circomlib), "-o", str(work)], work, commands)
    checked([snarkjs, "groth16", "setup", "aion.r1cs", str(ptau), "aion_0.zkey"], work, commands)
    checked([snarkjs, "zkey", "beacon", "aion_0.zkey", "aion.zkey", PUBLIC_BEACON_HEX, PUBLIC_BEACON_ITERATIONS], work, commands)
    checked([snarkjs, "zkey", "export", "verificationkey", "aion.zkey", "verification_key.json"], work, commands)
    checked([snarkjs, "groth16", "fullprove", "input.json", "aion_js/aion.wasm", "aion.zkey", "proof.json", "public.json"], work, commands)
    checked([snarkjs, "groth16", "verify", "verification_key.json", "public.json", "proof.json"], work, commands, 300)
    pub = json.loads((work / "public.json").read_text())
    pub[LENS["emitted"]] = "0" if pub[LENS["emitted"]] == "1" else "1"
    with tempfile.TemporaryDirectory(prefix="aion-generation-negative-") as tmp:
        public_bad = Path(tmp) / "public_bad.json"
        public_bad.write_text(json.dumps(pub), encoding="utf-8")
        neg = run([snarkjs, "groth16", "verify", "verification_key.json", str(public_bad), "proof.json"], work, 300)
    if neg.returncode == 0:
        fail("negative_check_passed")
    (work / "toolchain.receipt.json").write_text(json.dumps(tc, indent=2, sort_keys=True) + "\n")
    trace = receipt("generation-trace", {
        "generation_trace": commands,
        "trusted_setup_profile": "public_deterministic_beacon_demo_only",
        "public_beacon_hex": PUBLIC_BEACON_HEX,
        "public_beacon_iterations_exp": PUBLIC_BEACON_ITERATIONS,
        "negative_verify_returncode": neg.returncode,
    })
    (work / "generation-trace.receipt.json").write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    art = receipt("proof-artifacts", {
        "circuit_source_sha256": file_sha(ROOT / "aion.circom"),
        "input_sha256": file_sha(work / "input.json"),
        "verification_key_sha256": file_sha(work / "verification_key.json"),
        "proof_sha256": file_sha(work / "proof.json"),
        "public_sha256": file_sha(work / "public.json"),
        "generation_trace_receipt_hash": trace["receipt_hash"],
    }, [tc, trace])
    (work / "proof-artifacts.receipt.json").write_text(json.dumps(art, indent=2, sort_keys=True) + "\n")
    return art


def cycle(query: bytes, corpus: list[bytes]) -> tuple[bytes, str]:
    host = run_host_route(query, corpus)
    return host["emitted"], host["transcript_root"]


def statement(transcript_root: str, proof_root: str, artifact: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": "aion-cycle-statement-v1",
        "cycle_id": "aion.one_prompt_closed_loop.v1",
        "policy": "aion.cycle.v1",
        "expected_transcript_root": EXPECTED_TRANSCRIPT_ROOT,
        "transcript_root": transcript_root,
        "proof_root": proof_root,
        "proof_system": "groth16",
        "circuit_hash": artifact["circuit_source_sha256"],
        "verification_key_hash": artifact["verification_key_sha256"],
        "public_input_hash": artifact["public_sha256"],
        "proof_hash": artifact["proof_sha256"],
    }
    payload["cycle_root"] = sha256_hex(canonical_bytes(payload))
    return payload


def execute() -> None:
    fx = json.loads((ROOT / "fixtures" / "canonical.json").read_text())
    q = fx["query"].encode("utf-8", "strict")
    corpus = [c.encode("utf-8", "strict") for c in fx["corpus"]]
    emitted, root = cycle(q, corpus)
    if root != EXPECTED_TRANSCRIPT_ROOT:
        fail("expected_transcript_root_mismatch")
    _, replay = cycle(q, corpus)
    if replay != root:
        fail("replay_mismatch")
    tq = bytearray(q); tq[0] ^= 1
    _, tamper = cycle(bytes(tq), corpus)
    if tamper == root:
        fail("tamper_not_detected")
    art = prove(build_input(q, corpus, emitted, root))
    st = statement(root, art["receipt_hash"], art)
    (ROOT / "aion.statement.json").write_text(json.dumps(st, indent=2, sort_keys=True) + "\n")
    write_emission_chain(st)
    write_phase_receipts(st)



def verify_receipt_hash(obj: dict[str, Any]) -> str:
    claimed = obj.get("receipt_hash")
    if not isinstance(claimed, str) or len(claimed) != 64:
        fail("receipt_hash_missing")
    body = dict(obj)
    body.pop("receipt_hash", None)
    actual = sha256_hex(canonical_bytes(body))
    if actual != claimed:
        fail("receipt_hash_mismatch")
    return claimed


def load_verified_receipt(path: Path) -> dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    verify_receipt_hash(obj)
    if obj.get("proof_passed") is not True:
        fail("receipt_not_passing")
    return obj


def recompute_artifact_receipt(tool: dict[str, Any], existing: dict[str, Any], trace: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "circuit_source_sha256": file_sha(ROOT / "aion.circom"),
        "input_sha256": file_sha(BUNDLE_DIR / "input.json"),
        "verification_key_sha256": file_sha(BUNDLE_DIR / "verification_key.json"),
        "proof_sha256": file_sha(BUNDLE_DIR / "proof.json"),
        "public_sha256": file_sha(BUNDLE_DIR / "public.json"),
        "generation_trace_receipt_hash": trace["receipt_hash"],
    }
    return receipt("proof-artifacts", payload, [tool, trace])


def bits_to_hex(bits: list[Any]) -> str:
    if len(bits) != 256:
        fail("public_digest_bit_count_mismatch")
    value = 0
    for bit in bits:
        b = int(bit)
        if b not in (0, 1):
            fail("public_digest_bit_not_boolean")
        value = (value << 1) | b
    return f"{value:064x}"


def verify_statement(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    cycle_root = data.get("cycle_root")
    body = dict(data)
    body.pop("cycle_root", None)
    if sha256_hex(canonical_bytes(body)) != cycle_root:
        fail("cycle_root_mismatch")
    checkpoint("statement cycle_root recomputed from body")
    if data.get("transcript_root") != EXPECTED_TRANSCRIPT_ROOT:
        fail("transcript_root_mismatch")
    checkpoint("transcript_root matches frozen EXPECTED_TRANSCRIPT_ROOT")

    tool = load_verified_receipt(BUNDLE_DIR / "toolchain.receipt.json")
    trace = load_verified_receipt(BUNDLE_DIR / "generation-trace.receipt.json")
    existing_artifact = load_verified_receipt(BUNDLE_DIR / "proof-artifacts.receipt.json")
    if existing_artifact.get("child_receipt_hashes") != [tool["receipt_hash"], trace["receipt_hash"]]:
        fail("artifact_child_hash_mismatch")
    checkpoint("toolchain, generation-trace, and artifact receipts recomputed from bodies")
    recomputed = recompute_artifact_receipt(tool, existing_artifact, trace)
    if recomputed["receipt_hash"] != existing_artifact["receipt_hash"]:
        fail("artifact_receipt_recompute_mismatch")
    if recomputed["receipt_hash"] != data.get("proof_root"):
        fail("proof_root_mismatch")
    checkpoint("proof_root matches recomputed artifact receipt")
    if file_sha(ROOT / "aion.circom") != data.get("circuit_hash"):
        fail("circuit_hash_mismatch")
    if file_sha(BUNDLE_DIR / "verification_key.json") != data.get("verification_key_hash"):
        fail("verification_key_hash_mismatch")
    if file_sha(BUNDLE_DIR / "public.json") != data.get("public_input_hash"):
        fail("public_input_hash_mismatch")
    if file_sha(BUNDLE_DIR / "proof.json") != data.get("proof_hash"):
        fail("proof_hash_mismatch")
    checkpoint("circuit, verification key, public inputs, and proof file hashes match the statement")
    public_inputs = json.loads((BUNDLE_DIR / "public.json").read_text(encoding="utf-8"))
    digest_bits = public_inputs[LENS["emitted"]:LENS["emitted"] + 256]
    if bits_to_hex(digest_bits) != EXPECTED_TRANSCRIPT_ROOT:
        fail("public_digest_not_expected_transcript_root")
    checkpoint("public digest bits reconstruct EXPECTED_TRANSCRIPT_ROOT")

    snarkjs = resolve_tool("snarkjs")
    if not snarkjs:
        fail("missing_snarkjs")
    verify = run([snarkjs, "groth16", "verify", "verification_key.json", "public.json", "proof.json"], BUNDLE_DIR, 300)
    if verify.returncode != 0:
        fail("portable_verify_failed")
    checkpoint("Groth16 positive verification passed")
    bad_public = list(public_inputs)
    bad_public[LENS["emitted"]] = "0" if bad_public[LENS["emitted"]] == "1" else "1"
    with tempfile.TemporaryDirectory(prefix="aion-negative-verify-") as tmp:
        bad_reverify = Path(tmp) / "public_bad_reverify.json"
        bad_reverify.write_text(json.dumps(bad_public), encoding="utf-8")
        neg = run([snarkjs, "groth16", "verify", "verification_key.json", str(bad_reverify), "proof.json"], BUNDLE_DIR, 300)
    if neg.returncode == 0:
        fail("portable_negative_verify_passed")
    checkpoint("Groth16 negative verification rejected a flipped public input")
    transitions, final = load_emission_chain()
    verify_emission_lineage(data, transitions, final)
    checkpoint("emission lineage chain verified")
    verify_phase_receipts(data)
    checkpoint("phase receipts verified in order")

def _next_step(reason: str) -> str:
    if reason.startswith("missing_"):
        return "install the pinned toolchain with: make setup"
    if reason in {"portable_verify_failed", "portable_negative_verify_passed"}:
        return "regenerate the bundle with: make reproduce"
    return "restore the canonical artifact or regenerate with: make reproduce"


def main() -> int:
    import sys
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--verify-statement", type=Path)
    parser.add_argument("--explain", action="store_true")
    args = parser.parse_args()
    _EXPLAIN_CHECKS.clear()
    try:
        verify_statement(args.verify_statement) if args.verify_statement else execute()
    except Exception as exc:
        reason = failure_reason(exc)
        print("FAIL")
        print(f"FAIL_REASON:{reason}", file=sys.stderr)
        if args.explain:
            print(f"reason: {reason}", file=sys.stderr)
            print(f"next: {_next_step(reason)}", file=sys.stderr)
        return 1
    print("PASS")
    if args.explain:
        for label in _EXPLAIN_CHECKS:
            print(f"checked: {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
