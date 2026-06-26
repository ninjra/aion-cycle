# Contributing

This project is a map, not a framework. The best contribution is to test it.

1. Copy the prompt in the README into any coding agent.
2. Run the project it builds.
3. Break it on purpose: change one byte, one score, one receipt, or one circuit
   input.
4. If it ever prints `PASS` when it should fail, open an issue with the exact
   change you made.

Keep changes small and plain. The map should stay readable by someone with no
math or cryptography background. No hype, no jargon for its own sake.

## Contribution clamps

A useful contribution should preserve both clamps:

| Positive clamp | Negative clamp |
|---|---|
| Add a reproducible failing case. | Do not add a feature that only makes the demo pass. |
| Keep output `PASS`/`FAIL`. | Do not add explanatory output to the CLI. |
| Strengthen receipt recomputation. | Do not trust new self-attesting fields. |
| Improve fixed-canonical proof clarity. | Do not widen the claim to arbitrary production inputs. |
