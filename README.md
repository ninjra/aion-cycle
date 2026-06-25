Copyright 2026 Mushku Nobleworks. All rights reserved.
SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial

# AION Apex: The One-Prompt Closed Loop

Apex version: v1.0

AION is a small closed loop you can build on your own machine. Turn bytes into
bounded numbers, compare the numbers without names, keep receipts, map the
chosen field back, prove the closure relation with Groth16, and accept only if
the final bytes match.

It prints exactly one of these:

```text
PASS
```

or:

```text
FAIL
```

There is no halfway status.

You do not need advanced math to try it. You do not need a cryptography
background to read it. You do not need any private system to run it. Copy one
prompt into a coding agent, run the project it builds, then break it on purpose
and watch it refuse to lie.

## The whole map

AION is one closed path. One prompt builds the local project. The project runs
the path end to end. If every step closes, including a real Groth16 proof and
verification, it prints `PASS`. If anything is off, it prints `FAIL`.

There is no local-only pass. There is no optional proof. There is no demo mode.
The path is laminar: it flows once, cleanly, or not at all.

## The path

```text
Encode -> Carry -> Compare -> Carry Back -> Map Back -> Write -> Prove -> Verify
```

In plain language:

```text
turn bytes into bounded numbers
carry only the numbers
compare the numbers
carry the selected field hash back
look up the original bytes
write the exact bytes
prove the closure relation
verify the proof
```

AION watches the path and checks whether it closed. AION does not choose the
answer. AION does not change the answer. AION only checks whether the route
contradicted its own receipts.

## The five basic words

| Word | Plain meaning | Tiny math |
|---|---|---|
| Source bytes | The original input. | bytes are the domain |
| Field | A bounded integer view of bytes. | `F: bytes -> [-32768, 32767]^n` |
| Ledger | A private mapback table. | side information |
| Receipt | A hash record of one step. | `H(input, output, checks)` |
| Root | The final composite receipt hash. | parent commitment |

SHA-256 is a hash, not a digital signature. The comparison step receives fields
only. Identity returns only through the ledger.

## What each step does

| Step | Plain job |
|---|---|
| Encode | Turn source bytes into bounded numeric fields and store identity separately in the ledger. |
| Carry | Carry only copied numeric fields. Strip every label. |
| Compare | Compare fields with integer-only scoring and deterministic ranking. |
| Carry Back | Carry only the selected field hash back. |
| Map Back | Use the ledger to recover the selected source bytes. |
| Write | Emit output bytes exactly equal to the selected source bytes. |
| Prove | Generate a real Groth16 proof of the closure relation. |
| Verify | Verify the Groth16 proof and all local receipts. |
| AION | Accept only if the entire path closes. |

The proof is not in one step. The proof is in the whole path closing.

## The only promise

AION makes one narrow promise:

> If the generated project prints `PASS`, then the canonical route closed end to
> end: the selected bytes were mapped back and emitted exactly, the receipts
> composed, replay matched, tampering failed, the final root matched the frozen
> expected root, and a real Groth16 closure proof was generated and verified.

It does not prove:

- objective truth,
- production security,
- semantic understanding,
- patent scope,
- in-circuit SHA-256 computation.

It proves:

```text
local closed-loop integrity with real Groth16 closure verification
```

The final byte checks are direct and hashed:

```python
output_bytes == selected_source_bytes
sha256_bytes(output_bytes) == sha256_bytes(selected_source_bytes)
```

The final proof check is real:

```text
the Groth16 verifier accepts the closure proof
```

If the Groth16 circuit does not compile, prove, and verify, the result is
`FAIL`.

## The local scoring surface

The comparison step needs a surface that is small, deterministic, and easy to
inspect. This map uses a byte histogram:

- a list of 256 integer slots,
- one slot for each possible byte value from 0 to 255,
- for each byte in the source, add one to that byte's slot,
- clamp every value to the bounded range.

This is not a search engine. It is a tiny numeric surface that lets the loop
demonstrate the path: bounded fields, opaque carry, deterministic comparison,
mapback, exact output, and proof closure.

## The small math, in plain language

Nothing here is new mathematics. Each part is an ordinary, named result. Math is
not here to impress; it is here to point at the dimension plainly.

### Bounded numbers

```text
MIN = -32768
MAX =  32767
```

Keep every value inside a fixed range and clamp every operation. This is
fixed-width integer arithmetic.

### Compare fields

```text
score = sum(query[i] * record[i])
```

Multiply matching slots and add the results. This is the coordinate-wise product
and the inner product.

### Pick a winner

```text
key = (-score, field_hash)
```

Sort by score, then by hash, so every machine agrees on the order. This is a
total deterministic order.

### Keep receipts

```text
receipt = SHA256(canonical(input, output, checks))
```

Hash each step's record. This is a hash commitment.

### A green light cannot hide a red light

A parent receipt includes its child receipt hashes. If a child failed, the
parent fails. This is Merkle-style commitment composition.

### Names cannot leak

The comparison step receives fields only, never identity. Hidden identity must
not influence the result. This is noninterference.

### You cannot get something from nothing

A field alone does not reconstruct arbitrary source. Recovery needs the ledger
as side information. This is the source-coding limit, with descriptive
complexity as the lower-bound intuition.

### Prove closure compactly

Groth16 proves a small arithmetic relation over public values:

```text
final_root    == expected_root
selected_hash == output_hash
replay_root   == final_root
tamper_failed == 1
every child_passed bit == 1
```

This relation is mandatory. It is a real circuit, not a stub.

## The safety rules

1. Bytes are the source authority.
2. Fields are bounded integers.
3. Arithmetic is integer-only.
4. Every arithmetic result is clamped.
5. The comparison step sees only fields.
6. Identity lives only in the ledger.
7. Ranking uses a total deterministic key.
8. Ambiguous mapback fails instead of guessing.
9. Every step emits a receipt.
10. A parent receipt fails if any child failed.
11. Replay verifies; it does not mutate twice.
12. Final bytes must match directly, not only by hash.
13. The expected root is frozen in the project.
14. The tamper run must fail.
15. The Groth16 circuit must be real: no stub, no static boolean, no fake verifier.
16. Groth16 proof generation is required.
17. Groth16 verification is required.
18. `PASS` is allowed only after Groth16 verification passes.

## The real Groth16 circuit

The project includes a real minimal closure circuit. It does not fake Groth16
and it does not return a constant. It constrains the closure relation over public
field elements. The SHA-256 receipts are computed outside the circuit, and their
field-reduced roots are public circuit inputs.

```circom
pragma circom 2.1.6;

template AionClosure(n) {
    signal input expected_root;
    signal input final_root;
    signal input selected_hash;
    signal input output_hash;
    signal input replay_root;
    signal input tamper_failed;
    signal input child_passed[n];

    final_root === expected_root;
    selected_hash === output_hash;
    replay_root === final_root;
    tamper_failed === 1;

    for (var i = 0; i < n; i++) {
        child_passed[i] * (child_passed[i] - 1) === 0;
        child_passed[i] === 1;
    }
}

component main { public [
    expected_root,
    final_root,
    selected_hash,
    output_hash,
    replay_root
] } = AionClosure(6);
```

Production systems may add in-circuit hashing or a ZK-friendly hash layer. This
minimal circuit is still a real Groth16 closure gate, and the path requires it
to compile, prove, and verify.

## Copy-paste prompt

Paste the following into a coding agent that can write and run local files.

```text
Build a single local AION project with exactly two files:

  aion_cycle.py
  aion_closure.circom

Goal:
Run one laminar closed path and prove it:

  Encode -> Carry -> Compare -> Carry Back -> Map Back -> Write -> Prove -> Verify

The project must run with:

  python aion_cycle.py

It must print exactly PASS and exit 0 only if the entire path closes, including
real Groth16 proof generation and verification.
It must print exactly FAIL and exit 1 otherwise.
Print nothing else. Do not print the expected root. Do not print tracebacks
during normal failure handling. Do not write debug logs.

Use only the Python standard library for the loop. For the proof step, call real
external Groth16 tooling (circom and snarkjs) through subprocess. Do not install
or import third-party Python packages. If the Groth16 tooling is not available,
print FAIL. There is no demo mode and no local-only pass.

Required constants in aion_cycle.py:

  MIN_Q15 = -32768
  MAX_Q15 = 32767
  FIELD_SIZE = 256
  BOOTSTRAP_EXPECTED_ROOT = False
  EXPECTED_ROOT = "<concrete sha256 hex string>"

Determinism and integrity constraints:

1.  Never use Python's built-in hash(). Use hashlib.sha256 for all identity,
    ordering, receipts, and roots. Provide sha256_bytes(data: bytes) -> str.
2.  Serialize anything before hashing deterministically:
    json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    or strictly ordered tuples converted to bytes. Provide canonical_bytes(value).
3.  Bytes are the source authority. Encode any text fixtures as UTF-8 strict.
    Do not normalize casing, whitespace, line endings, or Unicode.
4.  Integer-only arithmetic. No float. No "/" division. Use "//" only if needed.
5.  Simulate fixed-width Q15: clamp every value to [MIN_Q15, MAX_Q15].
    Provide clamp_q15(x), sat_add(a, b), sat_mul(a, b). Python big integers must
    not hide overflow.
6.  Encode turns source bytes into a 256-slot byte histogram field. For each byte
    b in the source, increment slot b, then clamp. Store identity in a ledger
    mapping field_hash -> source_bytes.
7.  Carry copies a field to a pure list[int] and strips all metadata. The Compare
    step receives only list[int] fields. It must never receive dicts, ids, names,
    paths, text, raw bytes, or record hashes.
8.  Compare scores a query field against each corpus field:
    score starts at 0; for aligned slots, score = sat_add(score, sat_mul(q[i], c[i])).
9.  Rank by the total key (-score, field_hash) where
    field_hash = sha256_bytes(canonical_bytes(field)). Never rank by score alone.
10. Never rely on dict or set iteration order. Never iterate a set. Sort keys.
11. If two different source records produce the same field_hash, FAIL instead of
    guessing (ambiguous mapback).
12. Carry Back carries only the selected field_hash.
13. Map Back recovers selected source bytes from the ledger by selected field_hash.
14. Write emits output_bytes and requires both:
        output_bytes == selected_source_bytes
        sha256_bytes(output_bytes) == sha256_bytes(selected_source_bytes)
15. Every step emits a receipt dict: phase name, input hash, output hash, child
    receipt hashes, failed_checks list, proof_passed bool, receipt_hash.
16. A parent receipt fails if any child receipt failed. A green parent cannot
    hide a red child.
17. Compose all receipts into a final composite root.
18. Replay: run the canonical fixture twice. Selected bytes, output bytes, and
    final root must match. Track an event_id = sha256_bytes(canonical input);
    a repeated event_id is replay verification only and must not mutate twice.
19. Tamper: run a copied fixture with one byte, one score, or the selected
    record changed. That run must fail its root or byte-exact check.
20. The final composite root must equal the literal EXPECTED_ROOT. Do not compute
    EXPECTED_ROOT at runtime in the final file and do not update it at runtime.

Groth16 proof step (required, not optional):

21. Reduce each required hash to a circuit field element by taking
    int(hexdigest, 16) modulo the BN254 scalar field prime
    21888242871839275222246405745257275088548364400416034343698204186575808495617
    and pass it as a decimal string input.
22. Build the circuit input from the canonical run:
    expected_root, final_root, selected_hash, output_hash, replay_root,
    tamper_failed = 1, child_passed = [1, 1, 1, 1, 1, 1].
23. Write aion_closure.circom exactly as the AionClosure(6) template that asserts:
        final_root === expected_root
        selected_hash === output_hash
        replay_root === final_root
        tamper_failed === 1
        each child_passed bit is boolean and equals 1
    with public inputs expected_root, final_root, selected_hash, output_hash,
    replay_root.
24. Compile the circuit with circom, run a Groth16 setup, generate a proof with
    snarkjs groth16 fullprove (or prove), and verify it with snarkjs groth16
    verify, all through subprocess in a temporary working directory.
25. The project prints PASS only if: the canonical run passed, replay matched,
    the tamper run failed, the final root equals EXPECTED_ROOT, the circuit
    compiled, the proof generated, and the verifier returned OK. Otherwise FAIL.

Canonical fixture:

  query:
    b"need contract renewal approval"

  corpus:
    b"contract renewal requires finance approval"
    b"weather report says rain tomorrow"
    b"lunch menu includes soup"

  expected selected record:
    b"contract renewal requires finance approval"

Bootstrap then freeze EXPECTED_ROOT:

- While writing the project you may compute the canonical final root once.
- The final saved aion_cycle.py must contain a concrete EXPECTED_ROOT string and
  BOOTSTRAP_EXPECTED_ROOT = False.
- The final file must compare the current computed root against that literal and
  must never overwrite it at runtime.

Definition of done:
Running python aion_cycle.py on a machine with circom and snarkjs available
prints exactly PASS and exits 0. Changing any canonical input byte, any score,
any receipt, the selected record, or the circuit input causes FAIL and exit 1.
If circom or snarkjs is missing, it prints FAIL.
```

## Run it

```bash
python aion_cycle.py
```

Output:

```text
PASS
```

or:

```text
FAIL
```

## Break it

A green light is not enough. Break it on purpose:

- change one byte in the query,
- change one byte in the selected record,
- change one score,
- change one receipt,
- change one circuit input.

Run it again. It should print `FAIL`. The point is not that the path can pass.
The point is that it refuses to lie.

## What the local map leaves out

It does not leave out Groth16. Groth16 is part of the path. What it leaves out is
production scale:

- trusted setup ceremony details,
- production proof artifact storage,
- optimized field geometry,
- advanced scoring surfaces,
- production mapback storage,
- compiled projection.

None of that is needed to understand the map. Real Groth16 verification is still
required for `PASS`.

## The stones under the path

The whole path is made of ordinary, published parts:

| Part of the path | Standard result | Reference |
|---|---|---|
| Bounded numbers | Fixed-width integer arithmetic | Oppenheim and Schafer (2009); Knuth Vol. 2 (1997) |
| Coordinate compare | Hadamard product | Horn and Johnson (1991) |
| Match score and ranking | Inner product and stable sort | Halmos (1958); Strang (2016); Knuth Vol. 3 (1998) |
| Receipts | SHA-256 hash commitment | NIST FIPS 180-4 (2015) |
| Receipt tree | Merkle-style composition | Merkle (1988) |
| No name leakage | Noninterference / information flow | Goguen and Meseguer (1982); Denning and Denning (1977) |
| Mapback honesty | Source-coding and complexity bounds | Shannon (1948); Cover and Thomas (2006); Kolmogorov (1965) |
| Closure proof | Groth16 zk-SNARK | Groth (2016); Ben-Sasson et al. (2014) |

Kolmogorov complexity is a lower-bound idea, not a number the project computes.
Recovery is proven by the ledger, not by descriptive complexity.

## References

- Ben-Sasson, E., Chiesa, A., Tromer, E., and Virza, M. (2014). "Succinct Non-Interactive Zero Knowledge for a von Neumann Architecture." USENIX Security 2014.
- Cover, T. M., and Thomas, J. A. (2006). Elements of Information Theory, 2nd ed. Wiley.
- Denning, D. E., and Denning, P. J. (1977). "Certification of Programs for Secure Information Flow." Communications of the ACM, 20(7): 504-513.
- Goguen, J. A., and Meseguer, J. (1982). "Security Policies and Security Models." IEEE Symposium on Security and Privacy, 11-20.
- Groth, J. (2016). "On the Size of Pairing-Based Non-Interactive Arguments." EUROCRYPT 2016, LNCS 9666, 305-326.
- Halmos, P. R. (1958). Finite-Dimensional Vector Spaces, 2nd ed. Van Nostrand.
- Horn, R. A., and Johnson, C. R. (1991). Topics in Matrix Analysis. Cambridge University Press.
- Knuth, D. E. (1997). The Art of Computer Programming, Vol. 2: Seminumerical Algorithms, 3rd ed. Addison-Wesley.
- Knuth, D. E. (1998). The Art of Computer Programming, Vol. 3: Sorting and Searching, 2nd ed. Addison-Wesley.
- Kolmogorov, A. N. (1965). "Three Approaches to the Quantitative Definition of Information." Problems of Information Transmission, 1(1): 1-7.
- Merkle, R. C. (1988). "A Digital Signature Based on a Conventional Encryption Function." CRYPTO '87, LNCS 293, 369-378.
- National Institute of Standards and Technology (2015). FIPS PUB 180-4: Secure Hash Standard.
- Oppenheim, A. V., and Schafer, R. W. (2009). Discrete-Time Signal Processing, 3rd ed. Pearson.
- Shannon, C. E. (1948). "A Mathematical Theory of Communication." Bell System Technical Journal, 27(3): 379-423.
- Strang, G. (2016). Introduction to Linear Algebra, 5th ed. Wellesley-Cambridge Press.

## Patent and license

Patent pending. Public application details are intentionally omitted until a
publication record or approved citation is available.

This document is not a patent claim, not legal advice, and does not publish
private filing materials. The code you build from the prompt is yours to run
locally.

## Where to go

More information, demos, licensing, and contact: [mushku.com](https://mushku.com)

No account required to try the map. Copy the prompt and run it first.

## Last note

This is a map made of ordinary parts.

Copy it. Run it. Break it.

If it fails honestly, you found the door.
