# Security Policy

This repository is a single self-contained document (the README) plus standard
project files. It does not ship a service or a binary.

The map describes a local loop that you build and run on your own machine. It
makes one narrow promise: if the generated project prints `PASS`, the local
route closed and a real Groth16 closure proof verified. It does not claim
production security.

## Reporting

If you believe something in this document is wrong, unsafe, or misleading, or if
a project built from the prompt passes when it should fail, please open an issue
or contact us through https://mushku.com.

Do not include private keys, secrets, or sensitive data in reports.

## Known non-goals

The public README is a local integrity map. It is not a production security
claim. In particular, it does not claim:

- production-safe trusted setup,
- toolchain integrity,
- objective truth,
- semantic understanding,
- protection for sensitive data or critical infrastructure.

Reports are especially useful if they show that a generated project prints
`PASS` when one of the documented invariants is broken.

## Public safety clamps

| Positive clamp | Negative clamp |
|---|---|
| Inputs are untrusted data. | Inputs must not become instructions. |
| Verification policy is code and receipts. | Input text must not change verification policy. |
| Failure reports should be minimal. | Failure must not leak private data through debug output. |
| Reports should include reproducible failing cases. | Reports should not include secrets or private source data. |
