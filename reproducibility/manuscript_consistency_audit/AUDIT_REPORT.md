# AHCE-FL independent manuscript-to-results consistency audit

Audited UTC: 2026-11-07T00:56:18.660799+00:00
Manuscript: `manuscripts/IJAESD-345169/AHCE_FL_Final_Audited_Blind.docx`
DOCX SHA-256: `337094fc215f5c4a3c772e49a19763b79cbebd3ef1c574e1b47ca5c5d5c07c0d`

**Checks: 125/125 passed; 0 failed.**

## Primary evidence
- Independently checked all 51 source CSVs, each with 100 rounds.
- Recalculated accuracy, modeled bytes, cloud-sync events, paired 95% t intervals and unadjusted p-values for manuscript Tables 4–9.
- Verified flat direct-transfer baseline accounting explicitly excludes redundant cloud columns.
- Checked nine figure captions and presence of embedded images (not pixel-level chart accuracy).

## Limitations and provenance caveats
- Source experiment JSON configuration.method can report ahce-fl even when the top-level method is a different comparator. The separate actual method, filename and per-round logs define each group; this metadata discrepancy should be corrected in a future provenance-only update, without rewriting results.
- Historic EVIDENCE_REPORT.md uses 617120000 modeled bytes for flat baselines. The final manuscript uses 308560000 after excluding duplicate direct-transfer cloud entries. Interpret the two ledgers separately.
- All statistical contrasts rely on only three paired seeds; p-values are exploratory and require cautious interpretation.
- This audit validates internal numerical consistency, not external scholarly references, journal formatting, plot pixels or hardware energy/latency.

Configuration-method metadata mismatches: 12 JSON files.

## Failed checks
- None in the automated table/CSV checks.

## Git integrity
All analyzed CSVs include SHA-256 in `AUDIT_RESULTS.json`. The original manuscript and experiment files were not modified.
