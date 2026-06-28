# Circuit structure

Document class: public reference.

`aion.circom` is a single fixed-reference circuit for the v1 canonical fixture. It is
a fully-unrolled, machine-generated circuit: one `AionCycle()` template with explicit
per-index constraints and no loops. It is large and repetitive by construction. Audit
it through this structural spec, the structural regression test
(`tests/test_circuit_structure.py`), the host route, and the receipts — not by reading
all ~12k lines line by line.

## Inputs (fixed sizes)

- `query[30]`, `corpus0[42]`, `corpus1[33]`, `corpus2[24]`, `emitted[42]`: byte values.
- `*_bits[n][8]`: little-endian bit decompositions of each byte.
- `eq0[1260]`, `eq1[990]`, `eq2[720]`: pairwise equality indicators (query byte vs corpus byte).
- `eq0_inv`, `eq1_inv`, `eq2_inv`: inverse witnesses for the equality gadget.
- `ge01_bits[16]`, `ge02_bits[16]`: 16-bit range witnesses for the score comparisons.
- `expected_digest_bits[256]`: claimed SHA-256 digest bits.

## Public signals

```text
component main { public [emitted, expected_digest_bits] } = AionCycle();
```

## Constraint families (what is actually enforced)

1. Byte/bit consistency: each `*_bits[i][b]` is boolean and recomposes to the byte
   (`byte === Σ bit·2^b`).
2. Equality gadget: for each query/corpus byte pair,
   `eq <== 1 - (a-d)*inv`, `(a-d)*eq === 0`, `eq*(eq-1) === 0`.
   So `eq = 1` iff the bytes are equal, else `0`.
3. Score comparison: `score_k = Σ eq_k`. The circuit sets
   `ge01 <== score0 - 1 - score1` and `ge02 <== score0 - 1 - score2`,
   then binds each to a 16-bit decomposition (`ge0x === Σ ge0x_bits·2^i`,
   each bit boolean). This forces `score0 > score1` and `score0 > score2`,
   i.e. corpus0 is the strict winner.
4. Winner binding: `emitted[i] === corpus0[i]` for all bytes, so the emitted answer
   is exactly the winning record.
5. Transcript hash: `sha = Sha256(1480)` over the 185-byte domain-separated message
   (domain ‖ query ‖ corpus0 ‖ corpus1 ‖ corpus2 ‖ emitted), and
   `sha.out[i] === expected_digest_bits[i]` for all 256 bits.

## Soundness scope

Positive clamp:

- For the fixed fixture, the circuit enforces strict-winner selection, winner→output
  binding, and the SHA-256 transcript relation over the committed bytes.

Negative clamp:

- This is a fixed-shape circuit for one fixture; it is not a general argmax over
  arbitrary inputs.
- Circuit soundness is conditional on the trusted setup, which is demo/public only.
  See `TRUSTED_SETUP.md`. The committed proof verifies under the committed key; it is
  not a production soundness claim.
