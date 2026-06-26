# Public Boundary

This repository is public. It contains only the public AION reference artifact.

Allowed here:

- the fixed canonical reference cycle,
- the public circuit and proof bundle,
- public-safe setup and verification instructions,
- public-safe citations,
- public-safe patent-pending wording,
- reproducible tests and failure cases.

Not allowed here:

- private implementation names,
- private repository names,
- internal method inventories,
- private operational recovery records,
- private operational details,
- unpublished filing or non-public review details,
- private file paths,
- credentials or secret material,
- any claim wider than the fixed canonical reference route.

The public contract is simple:

```text
make setup
make verify
make test
```

If the route closes, it prints `PASS`. If anything fails, it prints `FAIL`.
