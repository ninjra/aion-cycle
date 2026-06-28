# Trusted Setup Boundary

Document class: public boundary.

AION v1 uses Groth16 for the fixed reference circuit. Groth16 has a circuit-specific setup step. This repository's setup is for a local reference artifact only.

## What this proves

Positive clamp:

- The committed proof verifies under the committed verification key.
- The verifier checks the statement, receipts, public inputs, artifact hashes, emission lineage, and phase receipts for the fixed canonical route.

Negative clamp:

- This does not prove production trusted-setup soundness.
- This does not prove objective truth, privacy, arbitrary-input support, or deployment security.

## What this does not prove

The demo setup is public and local-reference only. It must not be treated as:

- a production ceremony,
- a reusable security ceremony,
- a guarantee that no toxic waste exists,
- a hosted attestation,
- or a general provenance platform.

## Why this setup is demo-only

The repository is designed so readers can inspect and break the fixed route. It is not designed to establish a production Groth16 ceremony. Production use would require independent ceremony governance, operational controls, key custody policy, recovery planning, side-channel review, and deployment-specific security analysis.

## How to read PASS

`PASS` means the fixed reference route closed under the verifier available now. It is not a production cryptographic soundness statement.

## Demo key warning

Files under `proofs/v1/` are reference artifacts for this fixture. Treat key material and proof artifacts as demo/reference material, not production ceremony output.
