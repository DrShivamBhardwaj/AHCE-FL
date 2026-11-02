# MNIST 50-client validation — 2026-11-02

Three independent seeds: 11, 23, 42. 50 clients, 5 edges, 10 rounds, 2 local epochs, 5,000 training images, 1,000 test images. Non-IID Dirichlet alpha=0.5. All accuracy values are fractions, NOT percentages.

| Method | Threshold | Mean accuracy | Across-seed SD | Mean modeled bytes |
|---|---:|---:|---:|---:|
| fedavg | 0.01 | 0.315000 | 0.084717 | 61251200 |
| fedprox | 0.01 | 0.301000 | 0.085434 | 61251200 |
| fedcs | 0.01 | 0.419667 | 0.040673 | 61251200 |
| hfl | 0.01 | 0.315667 | 0.085757 | 45019632 |
| ahce-fl | 0 | 0.419667 | 0.040673 | 43896693 |
| ahce-fl | 0.01 | 0.177000 | 0.043578 | 28967808 |

Important: These are ten-round reduced-dataset validation outputs, not manuscript reproducibility or statistical proof of superiority. Model-based communication counts exclude TCP/IP packet framing. The tau=0.01 policy visibly harms test accuracy. No hardware latency or differential privacy has been measured.
