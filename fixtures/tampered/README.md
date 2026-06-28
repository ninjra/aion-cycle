# Fixture: tampered

Document class: public fixture.

Tampering examples are intentionally small changes to committed artifacts:

- statement root mutation,
- proof hash mutation,
- public input mutation,
- public digest bit mutation,
- receipt mutation,
- generation trace mutation.

The expected verifier output for each tamper is:

```text
FAIL
```

See `VERIFY.md` for the failure matrix.
