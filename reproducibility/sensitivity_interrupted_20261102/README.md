# Interrupted sensitivity experiment snapshot — 2026-11-02

Compression threshold tau=0, seed 11, CIFAR-10 full data. Saved 90 completed per-round metric records before process termination. **Partial only, not a complete experiment.** No model/optimizer state checkpoints were created by the existing implementation. It is impossible to continue training exactly from the saved last round. The next run must recompute this configuration from round 1.

The full validation/sensitivity runner skips only complete 100-round CSV files. Use `python -m ahce.sensitivity --mode compression --seeds 11 23 42` and then synchronization after compression completion.
