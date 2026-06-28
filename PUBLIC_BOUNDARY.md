# Public Boundary

Document class: public contract.

This repository is public. It contains only the public AION reference artifact.

## Public contract

```bash
make setup
make verify
make test
```

If the route closes, the verifier prints:

```text
PASS
```

If anything required for the fixed route fails, the verifier prints:

```text
FAIL
```

## Allowed here

- fixed canonical reference cycle,
- public circuit and proof bundle,
- public-safe setup and verification instructions,
- public-safe citations,
- public-safe patent-pending wording,
- reproducible tests and failure cases,
- public fixtures that demonstrate PASS/FAIL behavior,
- local read-only artifact viewing helpers.

## Not allowed here

- private implementation names,
- private repository names,
- internal Apex blueprints,
- internal method inventories,
- native internal Apex emissions,
- private durable-state fields or private restore pointers,
- private operational recovery records,
- unpublished filing or non-public review details,
- private file paths,
- credentials or secret material,
- any claim wider than the fixed canonical reference route.

## Allowed and forbidden public claims

| Claim | Allowed? | Why |
|---|---:|---|
| AION v1 is a local reference implementation. | Yes | Matches repository scope. |
| AION proves route truth for this fixed canonical cycle. | Yes | Bound by artifacts and verifier. |
| AION proves this output followed this committed path. | Yes | The narrow public claim. |
| AION proves objective truth. | No | Overbroad. |
| AION is a production provenance service. | No | Out of scope. |
| AION is private. | No | The fixture has public emitted bytes and public digest bits. |
| AION is a lie detector. | No | It verifies route closure, not intent. |
| AION verification fails closed when artifacts no longer cohere. | Yes | Covered by verifier and mutation tests. |

## Public/private egress rule

Internal Apex docs, method trackers, restore pointers, private durable-state fields, native internal
emissions, internal repo names, local paths, and non-public recovery records must
never be copied into this public repo.

## Sanitization checklist

Before public release, check:

```bash
make boundary-check
make test
```

The public boundary check rejects concrete private path and credential leaks.
Human review must also reject internal-only Apex method-tracker material and
claims wider than the fixed reference route.

## If in doubt

Use the narrower claim:

```text
AION proves route truth for this fixed reference cycle.
```

Do not use the broader claim:

```text
AION proves truth.
```


## Verification boundary

```text
Trust is ephemeral and lazy-resolved from source.
```

Public artifacts may be inspected and cached, but public verification must recompute the needed lineage, hashes, domain transitions, and chain links. A stored pass flag is not authority.

Reports, emissions, receipts, generated artifacts, and cache entries are snapshots, never authority unless explicitly promoted into durable data/source authority. Code/source files can be durable source artifacts. Trust comes only from fresh recomputation from source.

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
