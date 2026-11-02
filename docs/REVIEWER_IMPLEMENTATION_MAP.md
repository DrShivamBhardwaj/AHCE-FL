# Reviewer 2: implementation traceability

- Novelty: joint components implemented, but superiority versus recent methods remains to be shown with controlled ablations.
- Adaptive synchronization: explicit `should_sync(round, last_sync, divergence, maximum_gap, threshold)`. Cloud sync occurs at maximum gap or edge/global parameter divergence threshold.
- Selection: five normalized terms, including computing capability, each with an explicit configurable coefficient. Equal 0.2 coefficients are a provisional choice; sensitivity experiments are required.
- Compression: sparse float32 values and int32 flat indices, 8 bytes per retained element. Threshold 0.01 is retained from the manuscript, but ablations over thresholds are required.
- Architecture: two 3×3 Conv2d layers with 16 and 32 channels, followed by a 4×4 adaptive pooling layer, Dense(64), and logits(10). The runner emits trainable parameter count.
- Privacy: local raw samples stay within the simulator's client datasets; no DP or cryptographic secure aggregation implemented. Remove unsupported security guarantees and graphical labels.
- Metrics: client upload/download and edge-cloud upload/download are reported separately as model-level bytes. Latency is an analytic link model. Network packet loss is not simulated.
- Citation audit is editorial and cannot be established by software.
- Exact manuscript percentages are not embedded and must not be claimed without complete independent validation.
