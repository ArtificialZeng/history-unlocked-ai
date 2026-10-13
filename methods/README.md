# Reusable methods and known-answer controls

The indexed-cell resource is a self-contained, target-independent codec and
verifier. Its 11 frozen files are copied unchanged. It preserves literal tokens,
explicit lengths and source-supported distinctions; it rejects duplicate,
missing, malformed or out-of-range positions rather than silently repairing them.

Run with Node.js 22 or later:

```sh
node scripts/verify_methods.mjs
```

The runner verifies all input/software locks, checks three prewritten known-answer
fixtures and 30 refusal controls, and enumerates 364 token vectors under 12 order
variants (4,368 decode variants). A separate verifier reads the frozen controls
without calling the kernel. No historical source, target, language model, AI or
network is used. A software PASS does not establish applicability to an archive
item or calibrate historical success probability.

[API and frozen scope](indexed_cells/README.md) ·
[Mathematical specification](indexed_cells/MATHEMATICAL_SPEC.md)

Original project code and synthetic controls: copyright Zijian Zeng, 2026,
MIT under the repository licence. This release note sits outside the frozen
directory so the original locks remain valid.
