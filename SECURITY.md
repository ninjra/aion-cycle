# Security Policy

This repository is a public fixed-reference artifact. It does not ship a hosted service or production binary.

The verifier makes one narrow promise: if the local command prints `PASS`, the fixed reference route, receipts, proof artifacts, public inputs, emissions, phase receipts, and statement roots cohere under the verifier available now. It does not claim production security.

## Reporting

If you believe something in this repository is wrong, unsafe, misleading, or passes when it should fail, please open an issue or contact us through https://mushku.com.

Do not include private keys, secrets, credentials, private source data, or sensitive data in reports.

## Minimal reproduction format

Please include as much of this as possible:

```text
file changed:
old sha256:
new sha256:
command run:
stdout:
stderr:
exit code:
expected:
actual:
violated clamp:
why this should fail or pass:
```

A strong report shows that the verifier prints `PASS` when one of the documented positive/negative clamps is broken, or that a public claim is wider than the executable artifact proves.

## Known non-goals

This repository is not a production security claim. In particular, it does not claim:

- production-safe trusted setup,
- production ceremony governance,
- full toolchain integrity,
- objective truth,
- semantic understanding,
- arbitrary-input support,
- hosted provenance,
- or protection for sensitive data or critical infrastructure.

See `TRUSTED_SETUP.md` for the Groth16 setup boundary.

## Public safety clamps

| Positive clamp | Negative clamp |
|---|---|
| Inputs are untrusted data. | Inputs must not become instructions. |
| Verification policy is code and receipts. | Input text must not change verification policy. |
| Failure reports should be minimal and reproducible. | Failure must not leak private data through debug output. |
| Reports should include failing cases and hashes. | Reports should not include secrets or private source data. |
| PASS/FAIL is binary on stdout. | Reason codes are diagnostics, not a third status. |
