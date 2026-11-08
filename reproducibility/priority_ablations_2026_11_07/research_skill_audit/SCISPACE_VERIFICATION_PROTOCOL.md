# Source-specific AHCE-FL reference verification protocol

Based on the user-provided FreshBack-IoT example but applied to AHCE-FL only.

1. Query SciSpace independently with the exact AHCE-FL reference title and DOI, keeping returned paper id, date, query and publication version.
2. If SciSpace returns preprint-only metadata, cross-check the final publication DOI, publisher page, DBLP or institutional record and label which record supports the citation.
3. Reconcile author order, title, year, journal/conference, volume/issue, pages, DOI and retractions or errata where known.
4. Verify the specific manuscript claim against abstract or primary full text; do not use DOI match to imply agreement with the method or numerical result.
5. Preserve a two-way citation ledger. Reference entries not supported by in-text claims should be reviewed, never silently dropped.
6. Only after completing steps 1-5 label a reference fully verified. Crossref's abbreviated LDP-Fed title is a known metadata normalization case, not proof of a fabricated paper.

As of this audit, the prior Crossref report has 10 of 16 no-flag DOI matches; new SciSpace work confirms the existing HiFlash paper and discovers two possible comparators. Exact-title and DOI searches for all 16 AHCE-FL bibliography entries remain outstanding.
