# AHCE-FL: executable research simulator

An independent **PyTorch** implementation of Adaptive Hierarchical Communication-Efficient Federated Learning (AHCE-FL) derived from the submitted manuscript (IJAESD-345169).

## Experiment design

Client -> edge -> cloud weighted aggregation; deterministic Dirichlet non-IID partitions; resource-aware selection (bandwidth, energy, validation accuracy proxy, latency, and compute capacity); magnitude sparsification with index/value byte accounting; adaptive edge-cloud synchronization via a fully specified trigger; FedAvg, FedProx, FedCS and HFL controls.

**Important:** This is an operational reconstruction, not the original manuscript source. The manuscript does not state weights, exact scheduling triggers, CNN architecture, convergence definition, or serialization. These are explicit, configurable implementation choices. No privacy guarantee beyond local data handling is claimed; no differential privacy or secure aggregation is implemented.

## Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m ahce.train --config configs/smoke.json
python -m ahce.train --config configs/manuscript_mnist.json --method ahce-fl
python -m ahce.train --config configs/manuscript_mnist.json --method fedavg
python -m ahce.train --config configs/manuscript_mnist.json --method fedprox
python -m ahce.train --config configs/manuscript_mnist.json --method fedcs
python -m ahce.train --config configs/manuscript_mnist.json --method hfl
```

Outputs are written to `results/` as CSV and a JSON run manifest. Set `--method`, `--seed`, and `--tau` to run controls and compression ablations. Re-run with independent seeds for uncertainty estimates.

Training uses torchvision to load MNIST and CIFAR-10. Network latency, bandwidth, and compute times are **analytical estimates**, not packet-network or physical-hardware measurements. Simulation round duration is a modeled critical path, and excludes real GPU scheduling and TCP retransmission. First dataset load needs internet access.

### Manuscript configuration

50–200 clients, 5–10 edge servers, 100 rounds, 5 local epochs, batch size 32, learning rate 0.001, compression threshold 0.01, client fraction 0.2–0.5; heterogeneous bandwidth 5–100 Mbps, latency 10–100 ms, packet loss assumption 0.01. A configured 0.01 link loss is not a measured transport error rate.

**Research integrity:** The manuscript's 44.8% communication reduction, 30.9% latency reduction, 94.1% accuracy, and 43.1% faster convergence are historical *claims*, not outputs of this implementation. Do not present them as reproduced unless experimental runs independently confirm them. Reviewer 2's novelty, privacy, synchronization and cost-verification criticisms require empirical ablation studies and parameter-count disclosure.
