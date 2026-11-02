# CIFAR-10 verified download and AHCE-FL smoke execution

Dataset mirror: https://huggingface.co/datasets/MIT-OL-AI-D/cifar-10-python/resolve/main/cifar-10-python.tar.gz

Archive size: 170498071 bytes. MD5: c58f30108f718f92721af3b95e74349a. Torchvision loaded 50000 training and 10000 testing examples. Dataset files remain gitignored and are not uploaded to GitHub.

Experiment: configs/validation_cifar10.json, seed=42, method=ahce-fl, tau=0, 50 clients, 5 edges, 10 rounds, 1 local epoch, 2500 training and 500 test images.

Completed rounds: 10
Final accuracy: 0.118
Total modeled bytes: 46284000

Single-seed reduced-data smoke validation only. No manuscript-level efficacy claim is supported.
