# Fixture: tampered public digest bit

Document class: public fixture.

Mutation:

```text
flip one digest bit in proofs/v1/public.json after the emitted public bytes
```

Expected verifier output:

```text
FAIL
```

Reason:

```text
public digest bits no longer reconstruct EXPECTED_TRANSCRIPT_ROOT
```
