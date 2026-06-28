# Public Claims

Document class: public contract.

This file defines the claim vocabulary allowed for the public AION reference repo.

| Claim | Allowed? | Reason |
|---|---:|---|
| AION v1 is a local reference implementation. | Yes | Matches repository scope. |
| AION proves route truth for this fixed canonical reference cycle. | Yes | The proof and receipts bind this route. |
| AION proves this output followed this committed path. | Yes | This is the narrow claim. |
| AION has production Groth16 trusted-setup soundness. | No | The reference setup is public/demo-only and must not be read as a production ceremony. |
| The committed proof verifies under the committed verification key. | Yes | This is a verification fact, not a production soundness claim. |
| AION supports arbitrary inputs. | No | v1 is one fixed canonical fixture and fixed circuit shape. |
| AION proves objective truth. | No | Overbroad. |
| AION is a production provenance service. | No | Production ceremony and deployment are out of scope. |
| AION is private. | No | The reference fixture has public emitted bytes and public digest bits. |
| AION is a lie detector. | No | It verifies route closure, not human intent. |
| AION verification fails closed when artifacts no longer cohere. | Yes | Covered by verifier and mutation tests. |
| AION is AI-powered. | No | Misleading and unsupported by the reference artifact. |

## Preferred public wording

Use:

```text
AION proves route truth: this output followed this committed path.
```

Avoid:

```text
AION proves truth.
```

## Boundary rule

No public claim may rely on internal Apex docs, internal method trackers, private durable-state fields, private repo names, private file paths, or non-public recovery records.

## Positive and negative claim pairs

Every major public claim states what it is and what it is not.

| Topic | Positive claim | Negative clamp |
|---|---|---|
| Route truth | This output followed this committed path. | It does not prove objective truth, intent, or semantics. |
| Local-first | Verification runs locally and fail-closed. | It is not a hosted or production provenance service. |
| Receipts | Receipts are recomputed from artifacts and bodies. | A `proof_passed` flag is never trusted by itself. |
| Proof | Groth16 verifies the fixed canonical circuit under the committed verification key. | It does not provide production trusted-setup soundness or prove anything outside that circuit. |
| PASS | PASS means the fixed cycle closed end to end. | PASS is not security, privacy, or production readiness. |
| FAIL | FAIL means a required relation did not cohere. | FAIL is not a partial success or best-effort result. |
| Artifacts | Artifacts are inspectable current snapshots. | Reports/generated artifacts are snapshots, not durable authority; code/source files can be durable source artifacts. |
| Cache | Caches may store reusable material. | Caches may not store or replay trust. |
| Determinism | Re-running the fixed host route reproduces the transcript relation; proof verification is checked locally. | It does not claim arbitrary-input determinism or production ceremony soundness. |
| Sections | Any valid section can re-enter verification. | Orphan, copied, or wrong-cycle sections are invalid. |

<!-- AION_INVARIANT_PROJECTION_START -->
## AION invariant projection

Invariant: `aion-trust-lineage-storage-v1`
Version: `2026-06-27`
Packet hash: `7dc4cfd6d5df39ba3dc3234456f62f64f8aeae71448f3cb56d604e919e3ab696`
Document class: public projection

Positive clamp:

- AION verifies present state from source lineage.
- Code/source files may be durable source artifacts; durable data/context stores preserve material and lineage.
- Reports, emissions, receipts, generated artifacts, and caches are inspectable current snapshots unless explicitly promoted.
- Every major public claim says what it is and what it is not.

Negative clamp:

- Reports, receipts, emissions, generated artifacts, and caches are not authority unless explicitly promoted into durable data/source authority.
- Nothing is trusted because it exists, is stored, is emitted, is cached, is signed, is hashed, or says it passed.
- Public docs must not make internal scientific-metaphor claims or expose private implementation details.
<!-- AION_INVARIANT_PROJECTION_END -->
