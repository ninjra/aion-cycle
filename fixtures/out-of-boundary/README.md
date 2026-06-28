# Fixture: out of boundary

Document class: public fixture.

This fixture describes material that must not appear in the public reference repo:

- private file paths,
- credentials,
- private keys,
- internal Apex blueprints,
- internal method inventories,
- private recovery records,
- claims wider than the fixed reference route.

Run:

```bash
make boundary-check
```

Expected: the public boundary test passes only if none of that material is present.
