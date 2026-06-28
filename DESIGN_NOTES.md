# Design Notes

Document class: public rationale.

These notes explain why the public reference is narrow. They are not additional claims.

## Why fixed reference cycle?

A fixed cycle lets readers inspect every part of the route. The goal is not broad product coverage; the goal is a small artifact that can be recomputed and broken on purpose.

## Why local-first?

Local-first execution keeps the public reference independent of a hosted service. The verifier should not require a private backend to decide `PASS` or `FAIL`.

## Why receipts?

Receipts make each step accountable to inputs, outputs, child receipts, failed checks, and artifact hashes. A green flag is not enough; the verifier recomputes the receipt relation.

## Why three roots?

AION separates:

- `transcript_root`: committed route bytes and emitted answer,
- `proof_root`: proof/toolchain/artifact receipts,
- `cycle_root`: final statement binding transcript root, proof root, and policy.

This avoids treating the final statement as a magic constant.

## Why Groth16 here?

Groth16 gives a compact proof for the fixed canonical circuit. In this reference, the setup is public/demo-only and not a production ceremony; see `TRUSTED_SETUP.md`. Do not read PASS as a production trusted-setup soundness claim.

## Why a generated circuit?

`aion.circom` is fully unrolled and machine-generated for the fixed fixture. It is large and repetitive by design. Auditability comes from the structural spec in `CIRCUIT.md`, the structural regression test, the host route, and the receipts, not from reading every constraint line. See `CIRCUIT.md`.

## Why fail closed?

AION has no partial-success state. If route, receipts, proof artifacts, public inputs, or roots no longer cohere, the result is `FAIL`.

## Why public emitted bytes?

The v1 fixture is public and fixed. The opacity claim is architectural noninterference: names and labels cannot steer comparison. It is not a general privacy claim.

## What would production require?

A production profile would need a real ceremony policy, deployment controls, operational recovery, key governance, side-channel analysis, and environment-specific security review. Those are outside this public reference.


## Why present-only trust?

Trust is ephemeral and lazy-resolved from source. AION treats past verification as evidence, not authority. The verifier resolves only the trust needed for the present decision, but resolves it all the way back to source lineage.

This is why caches may store bytes, fields, maps, and artifacts, but may not store trust. A cache hit must be re-hashed, re-linked, and re-verified before use.

Reports, emissions, receipts, generated artifacts, and cache entries are snapshots, never authority unless explicitly promoted into durable data/source authority. Code/source files can be durable source artifacts. Trust comes only from fresh recomputation from source.

## Rationale does not expand claims

These notes explain why the reference is narrow. They are rationale, not claims. Nothing here widens the positive claims or relaxes the negative clamps defined in `PUBLIC_CLAIMS.md`.

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
