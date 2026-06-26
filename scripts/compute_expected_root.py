#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR LicenseRef-Commercial
"""Compute the frozen AION v1 canonical transcript root."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = b"AION-CYCLE-V1|"


def select_winner(query: bytes, corpus: list[bytes]) -> int:
    cq = Counter(query)
    scores = [sum(cq[k] * Counter(c)[k] for k in cq) for c in corpus]
    if scores.count(max(scores)) != 1:
        raise RuntimeError("ambiguous_or_no_winner")
    return max(range(len(scores)), key=lambda i: scores[i])


def main() -> int:
    fixture = json.loads((ROOT / "fixtures" / "canonical.json").read_text(encoding="utf-8"))
    query = fixture["query"].encode("utf-8", "strict")
    corpus = [item.encode("utf-8", "strict") for item in fixture["corpus"]]
    emitted = corpus[select_winner(query, corpus)]
    digest = hashlib.sha256(DOMAIN + query + corpus[0] + corpus[1] + corpus[2] + emitted).hexdigest()
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
