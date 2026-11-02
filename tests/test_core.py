import numpy as np
import torch
from ahce.train import (partition_dirichlet, score_clients, sparsify,
                        should_sync, weighted_state, model)


def test_dirichlet_indices_conserved():
    y = np.arange(100) % 10
    partitions = partition_dirichlet(y, 8, 0.5, 42)
    assert sorted(np.concatenate(partitions).tolist()) == list(range(100))


def test_resource_score_rewards_better_client():
    r = {"bandwidth": [5, 100], "energy": [0.2, 1.0],
         "accuracy": [0.1, 0.9], "latency": [100, 10], "compute": [0.5, 2]}
    assert score_clients(r, [0.2] * 5)[1] > score_clients(r, [0.2] * 5)[0]


def test_sparsification_and_wire_bytes():
    d, n, active = sparsify({"a": torch.tensor([0.005, -0.02, 0.1])}, 0.01)
    assert torch.allclose(d["a"], torch.tensor([0, -0.02, 0.1]))
    assert (n, active) == (16, 2)


def test_aggregation():
    states = [{"w": torch.tensor([1.0])}, {"w": torch.tensor([3.0])}]
    assert torch.allclose(weighted_state(states, [1, 3])["w"], torch.tensor([2.5]))


def test_sync_guards():
    assert not should_sync(1, 0, 0.01, 3, 0.05)
    assert should_sync(3, 0, 0.01, 3, 0.05)
    assert should_sync(1, 0, 0.06, 3, 0.05)


def test_models_have_valid_outputs():
    assert model("mnist")(torch.zeros(2, 1, 28, 28)).shape == (2, 10)
    assert model("cifar10")(torch.zeros(2, 3, 32, 32)).shape == (2, 10)
