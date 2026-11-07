# P2/P3 paired reproducibility synthesis

All 45 archived source cases passed 100-round, seed, configuration and SHA-256 integrity checks.
The main study's 51 archived runs and its original tables were not overwritten.
Reported confidence intervals are two-sided Student t intervals (n=3); accuracy differences are candidate minus equal-weight or timer-control reference. Holm adjustments are within P2 or P3 comparison families.
No inference about hardware radio, energy, packet overhead, privacy or deadline reliability follows from modeled bytes.

## P2: client-selection weight ablation

| Selection emphasis | Mean final accuracy | 95% CI | Mean modeled bytes | Mean syncs | Δ accuracy vs equal | Paired p | Holm p |
|---|---:|---|---:|---:|---:|---:|---:|
| equal | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | control | — | — |
| bandwidth | 0.485500 | [0.473430, 0.497570] | 366214077 | 100.0 | +0.012433 | 0.19144 | 0.76576 |
| energy | 0.473467 | [0.428828, 0.518105] | 371286365 | 100.0 | +0.000400 | 0.95856 | 0.97161 |
| accuracy | 0.488033 | [0.413368, 0.562698] | 357693709 | 100.0 | +0.014967 | 0.48580 | 0.97161 |
| latency | 0.494700 | [0.430583, 0.558817] | 373089776 | 100.0 | +0.021633 | 0.06520 | 0.32598 |
| compute | 0.492067 | [0.438107, 0.546026] | 360925949 | 100.0 | +0.019000 | 0.22955 | 0.76576 |

## P3: synchronization gap × divergence threshold

| Gap G | Threshold δ | Mean final accuracy | 95% CI | Mean modeled bytes | Mean syncs | Δ accuracy vs G=1, δ=10⁹ | Holm p |
|---:|---:|---:|---|---:|---:|---:|---:|
| 1 | 0.05 | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | identical outcomes; t-test undefined | — |
| 1 | 0.5 | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | identical outcomes; t-test undefined | — |
| 1 | 1e+09 | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | control | — |
| 3 | 0.05 | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | identical outcomes; t-test undefined | — |
| 3 | 0.5 | 0.476733 | [0.439218, 0.514248] | 332182613 | 76.7 | +0.003667 | 0.11516 |
| 3 | 1e+09 | 0.475467 | [0.448180, 0.502753] | 273122664 | 33.0 | +0.002400 | 0.85423 |
| 5 | 0.05 | 0.473067 | [0.433701, 0.512432] | 366004619 | 100.0 | identical outcomes; t-test undefined | — |
| 5 | 0.5 | 0.476733 | [0.439218, 0.514248] | 332182613 | 76.7 | +0.003667 | 0.11516 |
| 5 | 1e+09 | 0.468167 | [0.443144, 0.493189] | 253395056 | 20.0 | -0.004900 | 0.85423 |

## Trigger telemetry (mean counts per run)

- G=1, δ=0.05: both=100, divergence=0, max_gap=0, held=0
- G=1, δ=0.5: both=53.6667, divergence=0, max_gap=46.3333, held=0
- G=1, δ=1e+09: both=0, divergence=0, max_gap=100, held=0
- G=3, δ=0.05: both=0, divergence=100, max_gap=0, held=0
- G=3, δ=0.5: both=0, divergence=76.6667, max_gap=0, held=23.3333
- G=3, δ=1e+09: both=0, divergence=0, max_gap=33, held=67
- G=5, δ=0.05: both=0, divergence=100, max_gap=0, held=0
- G=5, δ=0.5: both=0, divergence=76.6667, max_gap=0, held=23.3333
- G=5, δ=1e+09: both=0, divergence=0, max_gap=20, held=80

## Interpretation boundaries

- Baseline comparisons must not be conflated with resource-weight controls or the new crossed synchronization design.
- These are modeled communication payloads; wall-clock, physical radio loss and power were not independently validated.
- If divergence-triggered synchronization dominates the smaller thresholds, the maximum-gap parameter cannot be interpreted as an isolated cause of communication reduction.
- Figures 1–9 in the source manuscript remain unchanged until image-level validation.
