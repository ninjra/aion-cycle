Copyright 2026 Mushku Nobleworks. All rights reserved.
SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial

# AION Apex: The One-Prompt Closed Loop

Apex version: v1.0

AION is a small closed loop you can build on your own machine. Turn bytes into
bounded numbers, compare the numbers without names, keep receipts, map the
chosen field back, prove the fixed canonical cycle with Groth16, and accept only
if the final bytes match.

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

The proof is not in one step. The proof is in the fixed canonical path closing.

## The only promise

AION makes one narrow promise:

> If the generated project prints `PASS`, then the canonical route closed end to
> end: the selected bytes were mapped back and emitted exactly, the receipts
> composed, replay matched, tampering failed, the transcript root matched the frozen
> expected transcript root, and a real Groth16 proof of the fixed canonical cycle
> (route logic plus in-circuit SHA-256 of the transcript) was generated and
> verified.

It does not prove:

- objective truth,
- production security,
- semantic understanding,
- patent scope.

It proves:

```text
the fixed canonical cycle in zero knowledge, including in-circuit SHA-256
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
demonstrate the path: bounded fields, metadata-free carry, deterministic comparison,
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

The general design sorts by score and a deterministic tie-break. This v1 circuit
uses a stricter shape: the canonical fixture must have one unique winner. If the
winner is ambiguous, the run fails instead of guessing.

### Keep receipts

```text
receipt = SHA256(canonical(input, output, checks))
```

Hash each step's record. This is a hash commitment.

### A green light cannot hide a red light

A parent receipt includes its child receipt hashes. If a child failed, the
parent fails. This is Merkle-style commitment composition.

### Names cannot leak

The comparison step receives fields only, never names or labels. In v1, the
verifier sees the canonical public bytes because the circuit is a public fixed
fixture. The opacity claim is architectural: names and labels cannot steer the
comparison. This is noninterference.

### You cannot get something from nothing

A field alone does not reconstruct arbitrary source. Recovery needs the ledger
as side information. This is the source-coding limit, with descriptive
complexity as the lower-bound intuition.

### Prove closure honestly

The circuit asserts no free "pass" bit. There is no `tamper_failed === 1` and no
`child_passed === 1` witness, because asserting a public input equals a constant
is a tautology a prover could satisfy trivially.

Instead, every quantity the proof binds is computed by constraints:

```text
emitted[i] == corpus0[i]                     // exact output equals the winner
score0 - score1 >= 0   (16-bit range)        // strict winner, scored in-circuit
score0 - score2 >= 0   (16-bit range)
SHA256(transcript) == expected_digest_bits   // hashed in-circuit, public digest
```

The scores and the digest are produced inside the circuit, not handed in as free
witnesses. The emitted answer and the digest are public inputs, so the proof is
about real computed values, not a constant.


## Closure requirements

The local project must resolve the usual attack surfaces inside the path. These
are not future hardening notes. They are requirements for `PASS`.

- **Real Groth16 setup artifacts:** the project must generate real setup,
  proving-key, verification-key, proof, and public-input artifacts for the
  included closure circuit. The setup is local to the demo, but it must be real
  and hash-bound into the final receipt root.
- **Circuit soundness checks:** the circuit proves the route and the in-circuit
  SHA-256 commitment. The runner must run a verifier-negative check: flipping any
  public digest bit must make the real verifier reject the proof.
- **No fake verifier:** `PASS` is forbidden unless the real verifier returns OK
  for the untampered proof and rejects a tampered public input.
- **Toolchain binding:** the tool names, versions, and path hashes for `circom`,
  `snarkjs`, and `node` must be recorded in a toolchain receipt. The toolchain
  receipt hash is a child of `proof_root`. Public receipts use normalized command
  names and path hashes, not local absolute paths.
- **Artifact binding:** the circuit source hash, compiled artifacts, proving key,
  verification key, proof, public inputs, and verifier result are receipts.
  Historical command metadata is kept in a separate generation trace receipt.
  A missing or changed artifact or trace fails `proof_root`, which changes
  `cycle_root`.
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


## The three roots

AION uses three roots so the proof is not circular:

| Root | What it binds | How it is checked |
|---|---|---|
| `transcript_root` | the canonical bytes and emitted answer | computed by the host and by in-circuit SHA-256 |
| `proof_root` | toolchain, circuit source, compiled artifacts, keys, proof, public inputs, verifier result | computed from proof/artifact receipts |
| `cycle_root` | the final statement: transcript root + proof root + policy | recomputed from `aion.statement.json` |

`EXPECTED_TRANSCRIPT_ROOT` is frozen. The generated `cycle_root` is not a magic
constant; it is the hash of the emitted statement for that run. `PASS` requires
all three roots to cohere.

The portable verifier also parses `public.json` and reconstructs the 256 public
digest bits. Those bits must equal `EXPECTED_TRANSCRIPT_ROOT`, not merely hash to
the same `public.json` file. For the negative verifier check, it regenerates a
fresh bad public input from `public.json` and does not trust a stored
`public_bad.json`.

## The safety rules

1. Bytes are the source authority.
2. Fields are bounded integers.
3. Arithmetic is integer-only.
4. Every arithmetic result is clamped.
5. The comparison step sees only fields.
6. Identity lives only in the ledger.
7. The canonical fixture has a strict winner; ambiguous ranking fails.
8. Ambiguous mapback fails instead of guessing.
9. Every step emits a receipt.
10. A parent receipt fails if any child failed.
11. Replay verifies; it does not mutate twice.
12. Final bytes must match directly, not only by hash.
13. The expected transcript root is frozen in the project.
14. The tamper run must fail.
15. The Groth16 circuit must be real: no stub, no static boolean, no fake verifier.
16. Groth16 proof generation is required.
17. Groth16 verification is required.
18. `PASS` is allowed only after Groth16 verification passes.

## The Groth16 circuit

The project has one circuit, `aion.circom`. It proves the fixed canonical cycle
in zero knowledge. The canonical byte/scoring/output/hash relation is proved
in-circuit; the host remains responsible for fail-closed orchestration,
toolchain and artifact receipts, replay/tamper policy, and statement generation.

The circuit proves, in-circuit:

- every query, corpus, and output byte is a real byte (8-bit range checks),
- the score of each corpus record against the query is the count of matching
  byte pairs (the byte-histogram inner product, computed inside the circuit),
- corpus record 0 is the strict winner over records 1 and 2,
- the emitted output bytes equal the winning record byte for byte,
- the SHA-256 of the transcript `query || corpus0 || corpus1 || corpus2 ||
  emitted` equals a public 256-bit digest commitment.

The SHA-256 is computed inside the circuit using the widely used circomlib
`Sha256` template, with the exact installed package-lock and circuit-source hash
bound into the proof artifacts, so the proof itself attests the hash. The shape of the circuit:

```circom
// byte range check (per byte)
b[i] === sum(bits[i][k] * 2^k);     bits[i][k] * (bits[i][k] - 1) === 0;

// pairwise equality score (per query/corpus pair), eq in {0,1}
eq <== 1 - (q - c) * inv;     (q - c) * eq === 0;     eq * (eq - 1) === 0;

// strict winner: score0 - score1 and score0 - score2 are 16-bit non-negative
ge01 === sum(ge01_bits[k] * 2^k);

// exact output
emitted[i] === corpus0[i];

// in-circuit SHA-256 of the transcript, bound to the public commitment
sha = Sha256(1368);   sha.in[...] <== transcript_bits;   sha.out[k] === expected_digest_bits[k];
```

Public inputs are the emitted answer bytes and the 256-bit digest commitment. A
valid proof means: a witness exists for which the route logic holds and the
transcript hashes to exactly that public digest. The runner also performs a
verifier-negative check by flipping one public digest bit; the real verifier
must reject it.

There is no host-trusted hash step left in the proof. The host computes the same
digest only to know the public commitment and to fail closed before proving.

## Copy-paste prompt

Paste the following into a coding agent that can write and run local files.

```text
Build a single local AION project with these files:

  aion_cycle.py
  aion.circom
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
It must write aion.statement.json containing transcript_root, proof_root, and cycle_root.
Print nothing else. Do not print the expected transcript root. Do not print tracebacks
during normal failure handling. Do not write debug logs.

Use only the Python standard library for the loop. For the proof step, call real
external Groth16 tooling (circom and snarkjs) through subprocess. Do not install
or import third-party Python packages. If the Groth16 tooling is not available,
print FAIL. There is no demo mode and no local-only pass.

Required constants in aion_cycle.py:

  MIN_Q15 = -32768
  MAX_Q15 = 32767
  FIELD_SIZE = 256
  BOOTSTRAP_EXPECTED_TRANSCRIPT_ROOT = False
  EXPECTED_TRANSCRIPT_ROOT = "<concrete sha256 hex string>"

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
9.  For v1, require a strict unique winner. Do not use score-only ties; if the top score is tied, FAIL instead of guessing.
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
    transcript root must match. Track an event_id = sha256_bytes(canonical input);
    a repeated event_id is replay verification only and must not mutate twice.
19. Tamper: run a copied fixture with one byte, one score, or the selected
    record changed. That run must fail its root or byte-exact check.
20. The final composite root must equal the literal EXPECTED_TRANSCRIPT_ROOT. Do not compute
    EXPECTED_TRANSCRIPT_ROOT at runtime in the final file and do not update it at runtime.

Groth16 proof step (required, not optional):

21. Write aion.circom as one circuit that proves the fixed canonical cycle:
    a. 8-bit range checks for every query, corpus, and output byte;
    b. pairwise byte-equality scoring (the byte-histogram inner product) computed
       in-circuit for each corpus record;
    c. corpus record 0 is the strict winner (score0 - score1 and score0 - score2
       are non-negative 16-bit values);
    d. emitted output bytes equal the winning record byte for byte;
    e. in-circuit SHA-256 (widely used circomlib Sha256 template) of the transcript
       query || corpus0 || corpus1 || corpus2 || emitted equals a public 256-bit
       digest commitment.
22. Public inputs are the emitted answer bytes and the 256-bit digest commitment.
23. Install circomlib and compile with circom using the circomlib include path.
    Use a powers-of-tau large enough for the circuit (about 2^17).
24. Run a Groth16 setup, generate the proof with snarkjs, and verify it.
25. Run a verifier-negative check: flip one public digest bit; the real verifier
    must reject. If it accepts, FAIL.
26. The project prints PASS only if: the host cycle selected the strict winner,
    the emitted bytes equal the winner, replay matched, tampering changed the
    digest, the transcript digest equals the frozen EXPECTED_TRANSCRIPT_ROOT, the circuit
    compiled, the proof generated, the verifier returned OK, and the negative
    check rejected the tampered public input. Otherwise FAIL.

Canonical fixture:

  query:
    b"need contract renewal approval"

  corpus:
    b"contract renewal requires finance approval"
    b"weather report says rain tomorrow"
    b"lunch menu includes soup"

  expected selected record:
    b"contract renewal requires finance approval"

Bootstrap then freeze EXPECTED_TRANSCRIPT_ROOT:

- While writing the project you may compute the canonical transcript root once.
- The final saved aion_cycle.py must contain a concrete EXPECTED_TRANSCRIPT_ROOT string and
  BOOTSTRAP_EXPECTED_TRANSCRIPT_ROOT = False.
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
python3 aion_cycle.py --verify-statement aion.statement.json
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
- a fixed-length canonical fixture instead of arbitrary-length inputs,
- one in-circuit scoring surface instead of advanced scoring surfaces,
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
