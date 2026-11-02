# Mushku theorem-paper authorial voice standard

Author: S N Justin Ram  
Affiliation: Mushku Nobleworks  
ORCID: 0009-0008-3593-2816

This standard applies to every theorem paper in the series.

## Positive requirement

Each paper uses normal academic prose. The title page, author metadata, and
citation record identify S N Justin Ram as the author. The body does not need
to announce its own authorship.

Definitions, proofs, and scope statements use direct technical prose.
An ordinary first-person sentence is permitted when substantively useful, but
first person is never required merely to prove who wrote the paper.

Prefer the direct forms "Part B defines," "the selector determines," and "the
specified boundary." Avoid administrative substitutes such as "governs,"
"authorizes," or "earns credit" when a mathematical or evidentiary statement
is intended.

The preferred posture is: define the construction, state the theorem, give
the proof, and identify the exact scope. The paper does not announce that it
is ratified, immutable, governing, already proven, beyond challenge, or
authorized for publication. Those lifecycle facts belong in the release
packet or an explicitly marked archival artifact.

## Negative clamp

The paper must not call its author "the human" or "the user." It must not speak
from an assistant, agent, reviewer, approval-workflow, or external narrator's
perspective. It must not imply that an assistant wrote, owned, ratified, or
performed the author's theorem work. It must not insert a contrived
self-authorship declaration such as "I wrote this theorem"; the title page
already supplies attribution.

## Historical-artifact boundary

An immutable historical theorem source, receipt, quotation, or governance
artifact may preserve its exact original wording when separately identified as
an artifact. That wording does not control the manuscript's narrative voice.

If an exact historical source uses third-person workflow language, reproduce
it only inside a clearly marked archival appendix or separate artifact. Do not
project, paraphrase, or silently repair its wording inside the archival copy.
The reader-facing paper must remain independent of that historical voice.

Proof-only quantities should be described as not being execution evidence,
admission evidence, or implementation-conformance evidence. Do not narrate
ordinary mathematical distinctions using `credit`, `receipt-bound`, or
`progression` terminology.

## Verification gate

Every paper build must fail if its reader-facing narrative contains any of
these perspective-bearing forms:

- "The human has" or "the human has";
- "human-approved";
- "The user" or "the user";
- "the assistant";
- "the agent".

The gate must separately verify:

- normal academic prose and correct title-page attribution;
- absence of external-narrator or contrived self-authorship language in the
  reader-facing paper;
- byte-exact reproduction of any archival appendix;
- absence of self-certifying administrative language outside that appendix.

Passing typography, theorem equivalence, or artifact hashes cannot waive these
requirements.
