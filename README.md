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


## Closure requirements

The local project must resolve the usual attack surfaces inside the path. These
are not future hardening notes. They are requirements for `PASS`.

- **Real Groth16 setup artifacts:** the project must generate real setup,
  proving-key, verification-key, proof, and public-input artifacts for the
  included closure circuit. The setup is local to the demo, but it must be real
  and hash-bound into the final receipt root.
- **Circuit soundness checks:** the project must run at least one negative proof
  attempt or verifier-negative check for every circuit. Changing source bytes,
  output bytes, winner constraints, `final_root`, `selected_hash`,
  `output_hash`, `replay_root`, `tamper_failed`, or any `child_passed` bit must
  fail the proof path.
- **No fake verifier:** `PASS` is forbidden unless the real verifier returns OK
  for the untampered proof and rejects a tampered public input.
- **Toolchain binding:** the paths and versions (or `--version` output) for
  `circom`, `snarkjs`, and `node` must be recorded in a toolchain receipt. The
  toolchain receipt hash is a child of the final root.
- **Artifact binding:** the circuit source hash, compiled artifacts, proving key,
  verification key, proof, public inputs, and verifier result are all receipts.
  A missing or changed artifact fails the final root.
- **Receipt binding:** every receipt is meaningful only because it is generated
  by the step it describes and included in the parent root. The project must bind
  receipts to phase name, input hash, output hash, child receipt hashes, toolchain
  receipt hash where relevant, failed checks, and proof status.
- **Replay scope:** replay verifies the same event. It does not mutate state
  twice. The event id and replay root are part of the final closure relation.
- **No hidden output:** normal failure prints only `FAIL`. Internal failure
  details may be retained in local receipts, but they must not leak through the
  command-line result.
- **Fuzz smoke:** the generated project must include a small malformed-input
  smoke test: empty input, duplicate-field ambiguity, altered receipt, and bad
  circuit input must fail.

The point is not to describe risks. The point is to make the local path close
only when these risks are handled.

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

## The real Groth16 circuits

The project includes three real circuits. None of them fake Groth16, return a
constant, or pretend to prove SHA-256 internally.

The first circuit is the **full-cycle gate**. It proves the canonical tiny route
inside the circuit: byte range checks, byte-histogram-equivalent scoring,
selection of the winning record, and exact output equality. The checked-in file
is `aion_full_cycle.circom`.

The second circuit is the **field-root closure gate**. It gates the public
field-reduced transcript commitments used by the local verifier:

```circom
pragma circom 2.1.6;

template AionClosureRoot(n) {
    signal input expected_root;
    signal input final_root;
    signal input selected_hash;
    signal input output_hash;
    signal input replay_root;
    signal input canonical_transcript_root;
    signal input tamper_transcript_root;
    signal input tamper_failed;
    signal input child_passed[n];

    final_root === expected_root;
    selected_hash === output_hash;
    replay_root === final_root;
    canonical_transcript_root === final_root;
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
    replay_root,
    canonical_transcript_root,
    tamper_transcript_root
] } = AionClosureRoot(8);
```

The third circuit is the **digest-limb closure gate**. It checks full SHA-256
digest equality as four 64-bit limbs, so the equality statement is not only
"equal modulo the BN254 field prime." The SHA-256 computation still happens on
the host; this circuit constrains the host-computed digest limbs.

```circom
pragma circom 2.1.6;

template Bits64() {
    signal input value;
    signal input bits[64];
    var acc = 0;
    var pow = 1;
    for (var i = 0; i < 64; i++) {
        bits[i] * (bits[i] - 1) === 0;
        acc += bits[i] * pow;
        pow *= 2;
    }
    value === acc;
}

template DigestEq4() {
    signal input left[4];
    signal input right[4];
    signal input left_bits[4][64];
    signal input right_bits[4][64];

    for (var j = 0; j < 4; j++) {
        left[j] === right[j];
    }
}

template AionDigestLimbClosure(n) {
    signal input expected_root_limbs[4];
    signal input final_root_limbs[4];
    signal input selected_hash_limbs[4];
    signal input output_hash_limbs[4];
    signal input replay_root_limbs[4];
    signal input tamper_failed;
    signal input child_passed[n];

    for (var i = 0; i < 4; i++) {
        expected_root_limbs[i] === final_root_limbs[i];
        selected_hash_limbs[i] === output_hash_limbs[i];
        replay_root_limbs[i] === final_root_limbs[i];
    }

    tamper_failed === 1;
    for (var j = 0; j < n; j++) {
        child_passed[j] * (child_passed[j] - 1) === 0;
        child_passed[j] === 1;
    }
}

component main { public [
    expected_root_limbs,
    final_root_limbs,
    selected_hash_limbs,
    output_hash_limbs,
    replay_root_limbs
] } = AionDigestLimbClosure(8);
```

The README shows the short version of the digest-limb circuit. The repository
also includes `aion_digest_limb_closure.circom`, which adds explicit 64-bit
bitness constraints for each digest limb.

The path requires all three circuits to compile, prove, verify, and reject
tampered public inputs. The full-cycle circuit proves the tiny route itself. The
closure circuits prove the transcript/root relation around that route. The host
verifier still binds toolchain identity, artifact identity, receipts, replay,
and tamper transcripts into the final root.

## Copy-paste prompt

Paste the following into a coding agent that can write and run local files.

```text
Build a single local AION project with these files:

  aion_cycle.py
  aion_full_cycle.circom
  aion_closure_root.circom
  aion_digest_limb_closure.circom
  fixtures/canonical.json
  fixtures/tampered.json
  expected_root.txt
  toolchain.lock
  tests/test_redteam.py
  aion.statement.json

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

21. Build and prove aion_full_cycle.circom. This circuit must prove the canonical
    tiny route in-circuit: byte range checks for query/corpus/output bytes,
    byte-histogram-equivalent scoring by pairwise byte equality, selection of
    the winning record, and output bytes equal to the selected record.
22. Build two closure circuit inputs from the canonical run:
    a. field-reduced inputs for aion_closure_root.circom using each SHA-256
       digest reduced modulo the BN254 scalar field prime
       21888242871839275222246405745257275088548364400416034343698204186575808495617.
    b. four 64-bit limbs for each SHA-256 digest for
       aion_digest_limb_closure.circom, plus bit witnesses proving each limb is
       exactly 64 bits.
23. Write aion_closure_root.circom as the AionClosureRoot(8) template that gates:
        final_root == expected_root
        selected_hash == output_hash
        replay_root == final_root
        canonical_transcript_root == final_root
        tamper_failed == 1
        all eight child_passed bits are boolean and equal 1.
24. Write aion_digest_limb_closure.circom as the AionDigestLimbClosure(8)
    template that gates full digest equality over four 64-bit limbs for:
        expected_root == final_root
        selected_hash == output_hash
        replay_root == final_root
    and also gates tamper_failed and all eight child_passed bits.
25. Compile all three circuits with circom, run a Groth16 setup for each circuit,
    generate proofs with snarkjs, and verify all three proofs with snarkjs, all
    through subprocess in a temporary working directory.
26. The project prints PASS only if: the canonical run passed, replay matched,
    the tamper run failed, the final root equals EXPECTED_ROOT, all three circuits
    compiled, all three proofs generated, all three verifiers returned OK, and all
    verifier-negative checks rejected tampered public inputs. Otherwise FAIL.
27. Record a toolchain receipt containing the resolved paths and version outputs
    for circom, snarkjs, and node. Include its receipt hash in the final root.
28. Record artifact receipts for the circuit source, compiled circuit, setup
    artifacts, proving key, verification key, proof, public input, and verifier
    result. Include these receipt hashes in the final root.
29. Run a verifier-negative check by changing at least one public input after
    proof generation. The real verifier must reject it. If the tampered public
    input verifies, FAIL.
30. Run a circuit-input negative check for child_passed = [1, 1, 1, 1, 1, 0] or
    tamper_failed = 0. It must fail verification or produce a non-passing
    receipt. If it passes, FAIL.
31. Run malformed-input smoke checks: empty input, duplicate-field ambiguity,
    altered receipt, and bad circuit input must all fail. If any malformed case
    passes, FAIL.
32. Bind every phase receipt to phase name, input hash, output hash, child
    receipt hashes, failed checks, proof status, and the relevant toolchain or
    artifact receipt hash. A receipt not included in the parent root has no
    authority.
33. Emit aion.statement.json with: cycle_id, expected_root, final_root,
    selected_hash, output_hash, proof_system, both circuit hashes, both
    verification-key hashes, toolchain receipt hash, and final root. This is a
    portable statement suitable for later signing or transparency-log anchoring.
34. Include tests/test_redteam.py with negative tests for byte changes, score
    mutation, receipt mutation, circuit public input mutation, missing tools,
    duplicate field hash, corpus order permutation, hidden label changes,
    built-in hash() absence, and EXPECTED_ROOT not being recomputed at runtime.

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

The reference runner requires `node`, `circom`, and `snarkjs`, plus a Powers of
Tau file. A setup script installs the toolchain locally (no sudo) and fetches
and verifies the ptau:

```bash
make setup        # or: bash scripts/setup.sh
make verify       # or: python3 aion_cycle.py
```

Output:

```text
PASS
```

or:

```text
FAIL
```

If `node`, `circom`, `snarkjs`, or the ptau are missing, the runner fails closed
with `FAIL`. There is no local-only pass.

## Break it

A green light is not enough. Break it on purpose:

- change one byte in the query,
- change one byte in the selected record,
- change one score,
- change one receipt,
- change one circuit input.

Run it again. It should print `FAIL`. The point is not that the path can pass.
The point is that it refuses to lie.

## What the local map keeps small

It does not leave out Groth16. Groth16 is part of the path.

The local map keeps the rest small:

- local demo setup artifacts with hashes instead of a public ceremony,
- local proof artifacts committed or emitted with hashes instead of production artifact storage,
- the byte-histogram-equivalent full-cycle circuit instead of optimized field geometry,
- one scoring surface instead of advanced scoring surfaces,
- an in-memory ledger instead of production mapback storage,
- Python theorem execution instead of compiled projection.

None of that changes the path. Real Groth16 generation and verification are
still required for `PASS`.

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


## Where this fits

AION is not another manifest format. It is a fail-closed verifier policy around
bytes, fields, receipts, transformations, proof artifacts, and final output.
Other systems can say a manifest is well formed. AION asks whether the whole
route coheres. If any byte, receipt, replay, toolchain artifact, or proof no
longer agrees, the answer is `FAIL`.

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
