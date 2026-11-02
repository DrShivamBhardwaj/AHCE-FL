# CIFAR-10 full-validation protocol and reporting boundaries

- Dataset: all 50,000 CIFAR-10 training images and all 10,000 test images
- Common setting: 50 clients, 5 edges, 100 rounds, 5 local epochs, batch 32, learning rate 0.001, non-IID Dirichlet alpha 0.5
- Paired seeds: 11, 23, 42
- Comparisons: FedAvg, FedProx, FedCS, HFL and AHCE-FL
- Experimental design: same data partition seed per method and matched training settings. The simulator uses provisional equal resource-score weights.
- Compression sensitivity: tau = 0, 0.001, 0.01, 0.05. A threshold-specific 100-round sweep is separate from the primary matched comparison and must be verified on disk before inclusion.
- Synchronization sensitivity: maximum gap = 1, 2, 3, 5 rounds with explicit divergence thresholds. Each sensitivity configuration needs independent run identifiers.
- Statistical comparison: paired accuracy differences across fully completed seeds, mean, sample SD, two-sided paired Student t-test and 95% t confidence interval. Report effect sizes in percentage points and not relative percent.
- Model communication: sum of explicit client and cloud payload bytes. These are estimates of serialized payloads, not physical TCP/IP trace measurements.
- No statistical result may be reported when fewer than two paired seeds have completed. Three seeds give wide uncertainty and are exploratory, not decisive proof of superiority.
- Full baseline scripts: `python -m ahce.full_validation`, then `python -m ahce.statistics`. Runner skips only verified completed CSV files.
- Evidence status (as of initial launch 2026-11-02): full-data three-round pilot complete. Full 100-round multi-seed CIFAR-10 comparison NOT complete. No confidence intervals or p-values established.
- The manuscript's original 94.1% accuracy and claimed savings must not be presented as reproduced results.
