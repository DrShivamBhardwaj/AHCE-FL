# Full-dataset CIFAR-10 matched pilot

Date: 2026-11-02. Platform: single-process PyTorch simulator on an 8 GB Mac. This is **not** the requested 100-round, multi-seed confirmation.

Source config: `configs/full_cifar10_pilot.json`; 50 clients, 5 edge servers, 3 communication rounds, 5 local epochs, batch size 32, 0.001 learning rate, Dirichlet alpha 0.5, seed 42, 50,000 training images and 10,000 test images. AHCE-FL uses tau=0 in this pilot.

| Method | Rounds | Final accuracy | Modeled transmitted bytes |
|---|---:|---:|---:|
| fedavg | 3 | 0.3364 | 18513600 |
| fedprox | 3 | 0.3388 | 18513600 |
| fedcs | 3 | 0.2898 | 18513600 |
| hfl | 3 | 0.3377 | 13885200 |
| ahce-fl | 3 | 0.2903 | 13885200 |

The communication figures are analytical payload accounting and not measured TCP traffic. The FedCS and HFL baselines are simulator reconstructions. Client-resource scores use provisional equal weights. No cryptographic privacy mechanism is implemented. Statistical confidence intervals require independent seeds. AHCE-FL accuracy superiority is **not established**.

The full article needs new experiments before the original abstract claims can be retained.
