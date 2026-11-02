# Exact Typed Phase Chains with Recomputable Route Closure

This directory contains the candidate Paper V theorem, rendering, provenance,
and fail-closed publication packet.

The mathematical construction is defined by:

- `provenance/exact-typed-phase-chain-formal-specification-candidate.md`
- `exact-typed-phase-chains-with-recomputable-route-closure.tex`
- `exact-typed-phase-chains-with-recomputable-route-closure.pdf`

The current implementation is not equivalent to the candidate theorem. The
exact replacement and dependency-freeze requirements are recorded in
`provenance/OWNER-FREEZE-GATE.json`. Nothing in this directory authorizes
source mutation, publication, upload, DOI registration, or release.

Build with:

```bash
make -C papers pdf
```

Verify candidate paper checks with:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest \
  papers/tests/test_paper.py papers/tests/test_theorem_candidate.py -q --tb=short
```

## Public and private provenance

The `-PUBLIC.json` projections are the public provenance artifacts. Raw workspace records are retained in the private `aion-cycle-private-provenance` archive with exact byte identities and the original unpublished Git history. Raw records are excluded from this public repository. Regeneration tools resolve companion repositories relative to this workspace and require the corresponding owner inputs; missing private inputs do not authorize invented provenance.
