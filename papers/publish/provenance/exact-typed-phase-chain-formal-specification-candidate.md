# Exact Typed Phase-Chain Formal Specification

Author: S N Justin Ram  
Affiliation: Mushku Nobleworks  
Email: sram@mushku.com  
ORCID: 0009-0008-3593-2816

Status: candidate theorem source pending dependency freeze and equivalence to an
owner-frozen AION-cycle implementation theorem. This status record is release
metadata and is not a premise of the mathematics.

## 0. Exact imported boundaries

Fix a valid Ionizer epoch `A`. Import the exact Ionizer types and laws:

```text
Corpus_A                = U*
Tensor_A                = CanonicalTensor_A
Bytes_A                 = Image(Encode_A)
Phi_A                   : Corpus_A -> Tensor_A
Encode_A                = CanonicalEncoding_A
Decode_A                = CanonicalDecode_A
Encode_A                : Tensor_A -> Bytes_A
Decode_A                : Bytes* -> Tensor_A disjoint-union {REJECT}
Calculate_A             : Tensor_A x Tensor_A
                          -> Tensor_A disjoint-union {REJECT}
Resolve_A               : Tensor_A x Selector_A
                          -> Corpus_A disjoint-union {REJECT}
BloomAll_A(D)           = Resolve_A(D,ALL)
BloomAll_A(Phi_A(C))    = C
Phi_A(BloomAll_A(D))    = D                  for D in Tensor_A
Decode_A(Encode_A(D))   = D                  for D in Tensor_A
```

The second argument of `Calculate_A` is the canonical operation operand. No
outer opcode, phase label, or evaluator binding substitutes for it.

Import the exact Paper II owner signatures without widening their tuples:

```text
W_in,A(b) = (b_in,rho,d_in).
W_out,A(rho,d_in,b_out) = (b_return,d_out).
```

The main route instantiates those exact operators twice.  The independently
declared route-state products remain outside the owner return tuples:

```text
DataRouteState_A      = (rho_data,d_data,in,d_data,out)
OperationRouteState_A = (rho_operation,d_operation,in,d_operation,out)

W_data,in,A(b_data) = W_in,A(b_data)
                    = (b_data,in,rho_data,d_data,in) or REJECT
W_data,out,A(rho_data,d_data,in,b_result) = W_out,A(rho_data,d_data,in,b_result)
                    = (b_result,out,d_data,out) or REJECT

W_operation,in,A(b_operation) = W_in,A(b_operation)
                    = (b_operation,in,rho_operation,d_operation,in) or REJECT
W_operation,out,A(rho_operation,d_operation,in,b_operation) =
  W_out,A(rho_operation,d_operation,in,b_operation)
                    = (b_operation,echo,d_operation,out) or REJECT
```

where every payload is canonical tensor bytes. The data route carries the data
operand inward and the result outward. The operation route carries the
operation operand inward and returns the exact same canonical bytes as its
outward echo. Each route has its own derived `rho`, ingress digest, egress
digest, and complete `EXPECT_INGRESS -> ENGINE -> EXPECT_EGRESS -> DONE`
lifecycle. No operand is threaded around either crossing. Wire is identity on
each data projection and retains only transient route and digest evidence.

Import the exact Origamold bounded tensor-realization branch:

```text
Q                       = (q,b)
Realize_A(D,Q;R_A)      = (W_q,K_q) or REJECT
Read(W_q)               = beta_A,Lambda(D|q),
ConformingProfile_A(R_A),
0 <= |beta_A,Lambda(D|q)| <= b <= B_window.
```

This branch realizes a selected canonical tensor closure. It is not
`Resolve_A`, does not return an Ionizer language history, and is not an input
to the manifestation operator.

Import the exact Energizer manifestation boundary:

```text
Manifest_A,N(D,s,t) = PUBLISHED(t,len(C_s),H(C_s),B*,epoch(D),s)
                    or REJECT,
where C_s = Resolve_A(D,s).
```

Manifestation consumes `(D,s,t)` and performs the selected Ionizer mapback
inside its own boundary. It does not consume an Origamold window.

The calculation method is supplied by a calculation engine. Its internal
method is outside this specification. Ku is downstream and is not a premise.

## 1. Main route and exact phase types

The fixed main route is:

```text
Route_A = (
  IONIZE,
  ENCODE_DATA,
  WIRE_DATA_INGRESS,
  ENCODE_OPERATION,
  WIRE_OPERATION_INGRESS,
  DECODE_OPERANDS,
  CALCULATE,
  ENCODE_RESULT,
  WIRE_DATA_EGRESS,
  WIRE_OPERATION_EGRESS,
  DECODE_RESULT,
  RESOLVE,
  MANIFEST,
  CLOSE
).
```

For input `(C,D_operation,s,t)`, define the exact adjacent types:

```text
X_0  = Corpus_A x Tensor_A x Selector_A x Target_N
X_1  = Tensor_A x Tensor_A x Selector_A x Target_N
X_2  = Bytes_A  x Tensor_A x Selector_A x Target_N
X_3  = Bytes_A  x Tensor_A x Selector_A x Target_N x DataIngressState_A
X_4  = Bytes_A  x Bytes_A  x Selector_A x Target_N x DataIngressState_A
X_5  = Bytes_A  x Bytes_A  x Selector_A x Target_N
       x DataIngressState_A x OperationIngressState_A
X_6  = Tensor_A x Tensor_A x Bytes_A x Selector_A x Target_N
       x DataIngressState_A x OperationIngressState_A
X_7  = Tensor_A x Bytes_A x Selector_A x Target_N
       x DataIngressState_A x OperationIngressState_A
X_8  = Bytes_A x Bytes_A x Selector_A x Target_N
       x DataIngressState_A x OperationIngressState_A
X_9  = Bytes_A x Bytes_A x Selector_A x Target_N
       x DataEgressState_A x OperationIngressState_A
X_10 = Bytes_A x Bytes_A x Selector_A x Target_N
       x DataEgressState_A x OperationEgressState_A
X_11 = Tensor_A x Selector_A x Target_N
X_12 = Tensor_A x Selector_A x Target_N x Corpus_A
X_13 = ManifestReceipt_A,N
X_14 = RouteResult_A,N.
```

The phase equations are:

```text
IONIZE(C,D_operation,s,t)
  = (Phi_A(C),D_operation,s,t)

ENCODE_DATA(D_data,D_operation,s,t)
  = (Encode_A(D_data),D_operation,s,t)

WIRE_DATA_INGRESS(b_data,D_operation,s,t)
  = (b_data,D_operation,s,t,(rho_data,d_data,in))
    when W_data,in,A(b_data)=(b_data,rho_data,d_data,in)

ENCODE_OPERATION(b_data,D_operation,s,t,data_state)
  = (b_data,Encode_A(D_operation),s,t,data_state)

WIRE_OPERATION_INGRESS(b_data,b_operation,s,t,data_state)
  = (b_data,b_operation,s,t,data_state,
     (rho_operation,d_operation,in))
    when W_operation,in,A(b_operation)
         =(b_operation,rho_operation,d_operation,in)

DECODE_OPERANDS(b_data,b_operation,s,t,data_state,operation_state)
  = (Decode_A(b_data),Decode_A(b_operation),b_operation,s,t,
     data_state,operation_state)

CALCULATE(D_data,D_operation,b_operation,s,t,data_state,operation_state)
  = (Calculate_A(D_data,D_operation),b_operation,s,t,
     data_state,operation_state)

ENCODE_RESULT(D_result,b_operation,s,t,data_state,operation_state)
  = (Encode_A(D_result),b_operation,s,t,data_state,operation_state)

WIRE_DATA_EGRESS(b_result,b_operation,s,t,
                 (rho_data,d_data,in),operation_state)
  = (b_result,b_operation,s,t,(rho_data,d_data,in,d_data,out),
     operation_state)
    when W_data,out,A(rho_data,d_data,in,b_result)
         =(b_result,d_data,out)

WIRE_OPERATION_EGRESS(b_result,b_operation,s,t,data_state,
                      (rho_operation,d_operation,in))
  = (b_result,b_operation,echo,s,t,data_state,
     (rho_operation,d_operation,in,d_operation,out))
    when W_operation,out,A(rho_operation,d_operation,in,b_operation)
         =(b_operation,echo,d_operation,out)
     and b_operation,echo = b_operation byte for byte

DECODE_RESULT(b_result,b_operation,echo,s,t,evidence)
  = (Decode_A(b_result),s,t)

RESOLVE(D_result,s,t)
  = (D_result,s,t,Resolve_A(D_result,s))

MANIFEST(D_result,s,t,C_s)
  = receipt
    when Manifest_A,N(D_result,s,t)=receipt
     and ReadFinal_N(t)=C_s

CLOSE(receipt) = RouteResult_A,N(receipt).
```

Every equation is result-valued and propagates typed `REJECT`. Every adjacent
output has exactly the next input type. Both Wire route and digest states are
present in the applicable products and therefore in the canonical link
commitments. Consumed values are released or destroyed before the next
transition except for fields explicitly present in the next product. In
particular, `C` is absent after `IONIZE`, `D_data` is absent after `CALCULATE`,
the operation bytes are absent after their exact egress echo, and no vector of
all phase-boundary values is retained.

The route vector above is the only main route admitted by this theorem.
`FAKE`, `BOGUS`, a renamed phase, an inserted phase, a removed phase, a
reordered phase, or an otherwise well-typed alternate vector is outside
`Route_A` and returns typed `REJECT(RouteMismatch)`.

Each position `i` has one declaration:

```text
Phase_A[i] = (
  phase_id_i,
  index_i,
  input_type_i=X_i,
  output_type_i=X_(i+1),
  operator_binding_i,
  evaluator_binding_i
).
```

Well typing requires exact adjacent equality, epoch binding, fixed operators,
and fixed evaluators before execution.

## 2. Auxiliary bounded-realization section

Origamold is a separate typed section, not a fabricated bridge between
`Resolve_A` and `Manifest_A,N`:

```text
WindowSection_A(D,Q;R_A)
  = Realize_A(D,Q;R_A) = (W_q,K_q) or REJECT,
where Q=(q,b), ConformingProfile_A(R_A),
0 <= |beta_A,Lambda(D|q)| <= b <= B_window,
and Read(W_q)=beta_A,Lambda(D|q).
```

An AION route may bind this section to the same epoch and tensor identity as a
main-route tensor boundary. Its output type remains `Window_A`; it neither
changes `D` nor enters the dense selected-result route. Section evidence is
verified independently and may be referenced by identity, not substituted for
the main-route value.

## 3. Optional proof section

A proof section exists only when a fixed proof profile `P` is part of the route
declaration. Its exact contracts are:

```text
Statement_A,P  = CanonicalStatement(route_id_A,terminal_link,claim_P)
Prove_A,P      : Statement_A,P x ProverInput_A,P
                 -> ProofBytes_A,P disjoint-union {REJECT}
Verify_A,P     : Statement_A,P x ProofBytes_A,P
                 -> VerifiedStatement_A,P disjoint-union {REJECT}
```

If no proof profile is fixed, no `PROVE` or `VERIFY` phase appears, no profile
or prover value occurs in `X_0`, and `CLOSE` consumes only
`X_13=ManifestReceipt_A,N`. If a profile is fixed, the exact and only suffix is:

```text
X_13 = ManifestReceipt_A,N
X_14,P = ManifestReceipt_A,N x Statement_A,P x ProofBytes_A,P
X_15,P = ManifestReceipt_A,N x VerifiedStatement_A,P
X_16,P = RouteResult_A,N

PROVE(receipt)
  = (receipt,statement,proof)
    where statement=CanonicalStatement(route_id_A,h_12,claim_P)
      and proof=Prove_A,P(statement,ProverInput_A,P)

VERIFY(receipt,statement,proof)
  = (receipt,Verify_A,P(statement,proof))

CLOSE(receipt,verified_statement)=RouteResult_A,N(receipt).
```

`ProverInput_A,P`, `claim_P`, and the proof-system bindings are derived from
and fixed by the profile before execution. They are not free caller inputs.
The proof profile, its derived prover input, `PROVE`, and `VERIFY` are bound to
`route_id_A`. A profile-free route containing either proof phase, or a
profile-bound route missing, reordering, duplicating, or replacing either
phase, returns typed `REJECT(ProfileMismatch)`. This theorem binds the
declared relation only and does not enlarge the soundness claim of `P`.

## 4. Canonical value identities and exact equality

Every phase type `X` has one canonical encoding `Canonical_X : X -> B*` and
one type identifier:

```text
type_id(X) = H("AION-TYPE-V2" || epoch_A || canonical_type_description(X)).
```

For `x:X`, define evidence identity:

```text
value_id_A(X,x) =
  H("AION-VALUE-V2" || epoch_A || type_id(X) || Canonical_X(x)).
```

The executable and formal identities use exactly the `AION-ROUTE-V2`,
`AION-TYPE-V2`, `AION-VALUE-V2`, `AION-TYPED-LINK-V2`,
`AION-CHAIN-START-V2`, and `AION-TYPED-LINK-DIGEST-V2` domains.  A V1, V3,
unversioned, unhashed-type, or differently ordered body is not an alias and
returns typed rejection.

Exact phase and adjacency equality is always checked by byte equality of the
canonical typed values, or by identity of the same immutable typed boundary
object. Digest equality alone never establishes exact value equality.
`value_id_A` is commitment evidence only; its mutation-detection claim for
distinct unseen bytes is conditional on collision and second-preimage
resistance.

No record stores `source_record_id`, `field_to_records`, source bytes, a
retained mapback table, dictionary, pocket, grammar DAG, or external
restoration handle.

## 5. Route and entrypoint binding

Let `entry_A` be the fixed public entrypoint. Define:

```text
route_id_A = H(
  "AION-ROUTE-V2"
  || epoch_A
  || entry_A
  || Canonical(Route_A)
  || Canonical(Phase_A[0..n-1])
  || value_id_A(Tensor_A,D_operation)
  || Canonical((DATA_ROUTE,W_data,in,A,W_data,out,A))
  || Canonical((OPERATION_ROUTE,W_operation,in,A,W_operation,out,A))
  || selector_id_A(s)
  || target_namespace_id_N
  || optional_proof_profile_id
).
```

The route identifier is derived, not caller-selected. The canonical operation
operand is bound as data, not replaced by a phase opcode. The initial
predecessor is:

```text
h_-1 = H("AION-CHAIN-START-V2" || route_id_A || epoch_A || entry_A).
```

## 6. Phase evaluation and canonical link records

For `x_i:X_i`, the fixed evaluator returns exactly:

```text
Eval_A[i](x_i) = OK(x_(i+1)) or REJECT(reason_i).
```

Only `OK` creates a link.  The evaluator identity is derived from the actual declared callable
and is checked before evaluation together with its fixed
epoch, entrypoint, route identity, route input, and canonical phase position;
reusing an unchanged label with a substituted callable or evaluator environment
returns `REJECT(EvaluatorMismatch)`. Timeout,
unavailability, identity mismatch, exception, malformed input, or semantic
rejection returns its typed `REJECT` value, creates no successful link, and
creates no admitted aggregate chain.  `VerifyLink_A` and `VerifyChain_A` are
result-valued operators returning verified evidence or typed `REJECT`; neither
collapses the failure algebra to a Boolean.

For an admitted transition define:

```text
LinkBody_A[i] = CanonicalRecord(
  schema            = "AION-TYPED-LINK-V2",
  epoch             = epoch_A,
  entrypoint         = entry_A,
  route              = route_id_A,
  phase_id           = phase_id_i,
  phase_index        = i,
  chain_length       = n,
  input_type         = type_id(X_i),
  output_type        = type_id(X_(i+1)),
  operator_binding   = operator_binding_i,
  evaluator_binding  = evaluator_binding_i,
  predecessor        = h_(i-1),
  input_identity     = value_id_A(X_i,x_i),
  output_identity    = value_id_A(X_(i+1),x_(i+1)),
  status             = OK
)

h_i = H("AION-TYPED-LINK-DIGEST-V2" || LinkBody_A[i]).
```

The record contains commitments and declarations only. It contains no phase
value and no restoration authority.

## 7. Streaming verification and no retained boundary ledger

`VerifyLink_A` receives one current typed input, one current typed output, one
link, and the validated predecessor. It strictly parses the record, checks all
declarations, compares canonical typed bytes exactly, freshly evaluates the
declared relation, recomputes the evidence identities, and recomputes the link
digest. Any mismatch returns typed `REJECT`.

`VerifyChain_A(C,D_operation,s,t,links,terminal_result,expected_digest)` does
not accept a vector of boundary values. It derives the route, creates `x_0`,
and streams through the route with at most the current input and output values:

1. evaluate `x_(i+1)=Eval_A[i](x_i)`;
2. verify link `i` against those exact typed values;
3. release or destroy consumed `x_i` before advancing;
4. retain only `x_(i+1)`, the predecessor digest, and explicitly bounded
   transient operator state;
5. after the final phase, compare the exact terminal result and digest.

Link records never contain phase values. The verifier never retains the
complete boundary-value vector. Selector, target, operation tensor, transient
Wire evidence, and live values are included in the applicable memory and
lifetime accounting; they are not a hidden mapback ledger.

## 8. Section re-entry

A stored predecessor digest is not a validated anchor. A section from `j`
through `k` may re-enter only with:

```text
VerifiedPrefixAnchor_A = (
  route_id_A,
  epoch_A,
  entry_A,
  predecessor_index=j-1,
  exact_boundary_type=X_j,
  exact_boundary_value=x_j,
  predecessor_digest=h_(j-1),
  current_prefix_verification_receipt
).
```

The receipt must be produced by present verification of the complete prefix,
or by an independently verified certificate whose exact route, epoch,
entrypoint, boundary type/value, and predecessor are checked in the present.
An orphan digest, stale receipt, copied section, or cross-route/cross-epoch
anchor returns `REJECT`.

## 9. Datatype and aperture boundary

The patent fidelity ladder:

```text
sint16 -> sint8 -> sint4 -> sint2 -> sint1
```

and raw observation aperture ladder:

```text
1, 2, 4, 8, 16 bytes
```

are distinct. No phase has a universal `sint16` semantic premise. The route
permits no clipping, saturation, wrapping, truncation, lossy quantization,
collision acceptance, or silent cross-type coercion.

## 10. Main theorem

Fix a valid Ionizer epoch `A`, exact companion contracts, one canonical
operation tensor `D_operation`, selector `s`, target `t`, fixed route, and
well-typed deterministic phase declarations. Then:

1. every admitted transition has one canonical link body and digest;
2. local verification accepts only the exact declared typed relation;
3. whole-chain verification accepts only the fixed ordered route with exact
   canonical-byte boundary continuity;
4. deletion, insertion, reordering, duplication, cross-route use, cross-epoch
   use, entrypoint substitution, phase substitution, type mutation, value
   mutation, operation-operand mutation, selector mutation, target mutation,
   operator/evaluator mutation, terminal mutation, and trailing data reject;
5. a failed phase produces no admitted aggregate chain;
6. the accepted semantic result is exactly:

   ```text
   let D_data   = Phi_A(C)
   let b_data   = Encode_A(D_data)
   let (b_data,in,rho_data,d_data,in) = W_data,in,A(b_data)
   let b_operation = Encode_A(D_operation)
   let (b_operation,in,rho_operation,d_operation,in)
                  = W_operation,in,A(b_operation)
   let D_data,in      = Decode_A(b_data,in)
   let D_operation,in = Decode_A(b_operation,in)
   let D_result = Calculate_A(D_data,in,D_operation,in)
   let b_result = Encode_A(D_result)
   let (b_result,out,d_data,out)
                  = W_data,out,A(rho_data,d_data,in,b_result)
   let (b_operation,echo,d_operation,out)
                  = W_operation,out,A(
                      rho_operation,d_operation,in,b_operation)
   require b_operation,echo = b_operation byte for byte
   let D_out    = Decode_A(b_result,out)
   let C_s      = Resolve_A(D_out,s)
   let receipt  = Manifest_A,N(D_out,s,t)
   require foundation(receipt)=B*
   require epoch(receipt)=epoch(D_out)=A
   require selector(receipt)=s
   require target(receipt)=t
   require len(receipt)=len(C_s)
   require digest(receipt)=H(C_s)
   require ReadFinal_N(t)=C_s
   return RouteResult_A,N(receipt)
   ```

7. the auxiliary Origamold section, when used, returns exactly the selected
   tensor-closure image and is never substituted for `Resolve_A` or
   manifestation;
8. route evidence alone cannot restore any phase value; exact restoration
   remains exclusively at the imported Ionizer boundary;
9. section re-entry from a presently verified prefix agrees with the
   corresponding whole-chain segment;
10. digest evidence is separated from exact canonical-byte equality;
11. stored records, prior receipts, caches, and earlier success do not provide
   present acceptance;
12. no retained boundary-value vector, source ledger, or alternate mapback is
    admitted.

## 10.1 Patent foundation locators

The signed-as-filed patent is identified by SHA-256
`e2975c587ae6299f86a84e4630c51a4de19b72abfaf4ec45c853f68775418240`.
The following locators are technical provenance for the imported foundation;
they do not replace the exact phase-chain definitions above:

| Phase-chain leaf | Patent page / specification paragraph / claim locator |
|---|---|
| fixed epoch, operator, evaluator, route, and local transition boundary | PDF pp. 8-9 / spec pp. 4-5, paras. [0023]-[0025]; PDF p. 13 / spec p. 9, para. [0035]; PDF pp. 28-30 / spec pp. 24-26, paras. [0100]-[0109]; claims 12, 14, 19 |
| canonical typed representation and residual/fidelity preservation | PDF pp. 10-11 / spec pp. 6-7, paras. [0029]-[0030]; PDF pp. 17-21 / spec pp. 13-17, paras. [0058], [0060]-[0070]; claims 2, 9, 10, 17, 18 |
| strict validation, compatibility, and canonical terminal normal form | PDF pp. 7, 10 / spec pp. 3, 6, paras. [0018], [0029]; PDF pp. 18-19 / spec pp. 14-15, paras. [0060]-[0064]; claims 1, 2, 17 |
| exact encoding and logical byte identity | PDF p. 9 / spec p. 5, para. [0026]; PDF pp. 21-22 / spec pp. 17-18, paras. [0071]-[0075]; claims 3, 13 |
| selected exact mapback through `Resolve_A` | PDF p. 6 / spec p. 2, para. [0011]; PDF pp. 22-24 / spec pp. 18-20, paras. [0076]-[0080]; PDF pp. 33-34 / spec pp. 29-30, paras. [0120]-[0124]; claims 8, 20 |
| two-operand calculation boundary | PDF pp. 6-8 / spec pp. 2-4, paras. [0007], [0011]-[0012], [0022]-[0023]; PDF pp. 27-28 / spec pp. 23-24, paras. [0094]-[0099]; claims 8, 11, 16, 20 |
| no-smuggling and metadata/control separation | PDF pp. 5-6 / spec pp. 1-2, paras. [0004], [0009]; PDF p. 8 / spec p. 4, para. [0024]; PDF pp. 28-30 / spec pp. 24-26, paras. [0100]-[0109]; claims 12, 20 |
| fail-closed route and proof binding | PDF p. 6 / spec p. 2, para. [0010]; PDF p. 11 / spec p. 7, para. [0031]; PDF pp. 21-26 / spec pp. 17-22, paras. [0071]-[0089]; claims 5-7, 13-15, 19 |

## 11. Proof

Exact route typing follows by direct inspection of `X_0` through `X_14` and
the phase equations. Ionizer's second operand is encoded, transported inward,
decoded, consumed as canonical tensor data at calculation, and transported
outward unchanged. Its complete Wire lifecycle and the complete data/result
Wire lifecycle are distinct and both are bound into the route identity and
link sequence. Wire data transparency and Ionizer encode/decode identity
preserve both operands and `D_result`. The Resolve and Manifest equations use
the same `(D_out,s)` and exact byte equality establishes the terminal result.

Canonical link determinism follows from fixed declarations, field order,
canonical scalar encodings, and deterministic digest input. Streaming
verification establishes exact adjacency by canonical-byte comparison and
fresh evaluation, while hashes serve only as conditional tamper evidence.
Induction over route position proves ordered continuity and mutation
rejection. The memory discipline permits only the current transition values,
so no complete boundary ledger exists. Prefix re-entry is the same induction
started from a presently verified exact boundary anchor. The Origamold branch
retains its own exact codomain and therefore introduces no ill-typed bridge.

## 12. Scope

The theorem establishes exact typed route closure and mutation-detecting
evidence for the declared epoch and route. It does not establish objective
truth, permission, confidentiality, availability, calculation-engine safety,
network delivery, proof-system soundness beyond its stated premises, physical
erasure, or correctness outside the fixed route. Internal cross-repository
synchronization tooling is not a premise and is not a public dependency.
