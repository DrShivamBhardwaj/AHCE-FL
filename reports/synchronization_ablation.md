# Adaptive synchronization ablation (MNIST CPU, 2026-11-02)

Seed 42, 50 clients, 5 edges, 30 rounds, 2 local epochs, 5,000 training examples, 1,000 test examples. Threshold tau=0. Cloud sync is triggered only by the configured maximum gap because divergence threshold is set to 1000000.0.

| Setting | Successful rounds | Global syncs | Final accuracy | Modeled transmitted bytes |
|---|---:|---:|---:|---:|
| max gap 1 | 30 | 30 | 0.642000 | 137815200 |
| max gap 3 | 30 | 10 | 0.654000 | 107189600 |

One seed cannot support statistical superiority. Network latency is modeled rather than measured. These runs use a reduced training set and are not the full manuscript protocol.
