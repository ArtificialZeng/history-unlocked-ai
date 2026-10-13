# HC1679 — Audited conditional partial reading

A reproducible partial result from an HC Portal postcard, retained without letter repairs or a claim that the whole message is solved.

```sh
python3 -B code/check_release.py
```

Run inside `cases/hc1679` with Python 3.10+. The standard-library checker verifies saved evidence and forward/inverse certificates. It does not search keys, invoke AI or score new candidates.

The selected conditional transcription contains 289 source occurrences: 276 emitted positions and 13 separator exclusions. One global bijective mapping is mechanically consistent with all 276 selected positions. **15 unresolved or nonstandard spans remain, and the unchanged whole text is not coherent.** Four unobserved key assignments remain unidentifiable, with 24 equivalent permutations. The 36 retained source branches include 19 tested branches and 17 outside the trial, which are not falsified.

The original local artifact received independent reproducibility and scope review on 10 October 2026. That review disclosed a first-progress timing exception; passing a replay does not erase it or establish historical correctness, priority, an authentic key, or external expert acceptance. Continued solving stopped at a feasibility judgment of 75/100; this is not a calibrated probability.

This code-only derivative keeps required frozen inputs, 114 recorded trial outputs, the checker and component attribution. Images, the PDF, fonts, language-model derivatives and the earlier solver are omitted. Its manifest describes this derivative; `CORE_PROVENANCE.json` records byte-identical scientific inputs.

**Author:** Zijian Zeng, Institute of Computer Science and Digital Innovation, UCSI University, Kuala Lumpur, 56000, MALAYSIA.

The portable checker and original research contribution retain CC BY 4.0. This is not a blanket MIT licence grant over third-party sources. See `LICENSES/NOTICE.md`.
