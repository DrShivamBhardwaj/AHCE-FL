# Desktop Commander CPU execution: 2026-11-02

Device: Shivams-MacBook-Air, 8 GB RAM. Python 3.11 virtual environment.

Smoke-test scope: MNIST first 1,000 training examples, first 500 test examples, 5 clients, 2 edges, 2 clients selected per round, Dirichlet alpha=0.5, seed 42, 3 rounds, 1 local epoch, batch size 32.

Unit tests: 7 passed. Source commit before this report: e900381.

| Method | Final accuracy | Total modeled bytes over 3 rounds | Mean modeled critical-path ms |
|---|---:|---:|---:|
| AHCE-FL tau=0.0001 | 0.110 | 2756304 | 92.104 |
| FedAvg | 0.100 | 3675072 | 155.920 |

These are unreplicated smoke tests, not journal evidence. AHCE-FL falls back to dense client encoding when sparse index/value encoding exceeds model bytes. The FedAvg control was executed before the dense-fallback source change, but its uncompressed path is unaffected. Round duration is an analytic estimate, not observed network latency. Results do not validate manuscript claims or privacy guarantees.
