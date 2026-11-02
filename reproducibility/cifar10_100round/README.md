# CIFAR-10 100-round experiment artifacts

15 complete run CSV files, their JSON provenance records, paired statistical analysis, and SHA-256 hashes. Seeds: 11, 23, 42. Methods: FedAvg, FedProx, FedCS, HFL, AHCE-FL. All runs used 100 communication rounds with the manuscript CIFAR-10 configuration. The models are single-process simulation runs. Payload bytes are modeled, not physically measured traffic.

The CIFAR-10 raw dataset is excluded from Git. Source: CIFAR-10 Python dataset from Toronto, downloaded through a verified mirror, archive MD5 c58f30108f718f92721af3b95e74349a.

The AHCE-FL final accuracy was below all tested baselines. Consult analysis_summary.json for paired comparisons and confidence intervals.
