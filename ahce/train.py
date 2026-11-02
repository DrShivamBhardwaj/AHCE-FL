"""AHCE-FL: deterministic single-process federated simulation.

Network metrics are models, never measured packet traces. The scheduling rule and
selection weights are explicit implementation choices absent from the manuscript.
"""
import argparse
import copy
import csv
import json
import math
import random
import time
from pathlib import Path

import numpy as np


def partition_dirichlet(labels, n_clients, alpha, seed):
    if n_clients < 1 or alpha <= 0:
        raise ValueError("n_clients must be positive and alpha > 0")
    rng = np.random.default_rng(seed)
    y = np.asarray(labels)
    bins = [[] for _ in range(n_clients)]
    for klass in np.unique(y):
        ids = np.flatnonzero(y == klass)
        rng.shuffle(ids)
        split = rng.multinomial(len(ids), rng.dirichlet(np.full(n_clients, alpha)))
        for index, part in enumerate(np.split(ids, np.cumsum(split)[:-1])):
            bins[index].extend(part.tolist())
    return [np.asarray(v, dtype=np.int64) for v in bins]


def score_clients(resources, weights):
    """Five normalized factors: bandwidth, energy, accuracy, inverse latency, compute."""
    keys = ("bandwidth", "energy", "accuracy", "latency", "compute")
    w = np.asarray(weights, dtype=float)
    if w.shape != (5,) or (w < 0).any() or not np.isclose(w.sum(), 1):
        raise ValueError("selection_weights must have five nonnegative entries summing to 1")
    features = []
    for key in keys:
        data = np.asarray(resources[key], dtype=float)
        norm = (data - data.min()) / (np.ptp(data) + 1e-12)
        features.append(1 - norm if key == "latency" else norm)
    return w @ np.stack(features)


def sparsify(delta, tau):
    """Return dense decoded delta, wire bytes and selected-element count.

    Wire format: int32 flat index + float32 value (8 bytes per selected element).
    Real implementations need framing, tensor metadata and security overhead.
    """
    if tau < 0:
        raise ValueError("tau must be nonnegative")
    decoded = {}
    selected = 0
    for key, value in delta.items():
        array = value.detach().cpu()
        mask = array.abs() >= tau
        out = array * mask
        decoded[key] = out
        selected += int(mask.sum())
    return decoded, 8 * selected, selected


def weighted_state(states, counts):
    if not states or sum(counts) <= 0:
        raise ValueError("Nonempty states and positive total sample count required")
    total = float(sum(counts))
    return {key: sum(state[key].float() * (count / total)
                     for state, count in zip(states, counts))
            for key in states[0]}


def should_sync(round_number, last_sync, divergence, maximum_gap, threshold):
    """Cloud sync on max-gap expiry or large edge-to-cloud model divergence."""
    return (round_number - last_sync >= maximum_gap) or (divergence >= threshold)


def model(dataset):
    import torch.nn as nn
    channels = 1 if dataset == "mnist" else 3
    width = 28 if dataset == "mnist" else 32
    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.features = nn.Sequential(
                nn.Conv2d(channels, 16, 3), nn.ReLU(), nn.MaxPool2d(2),
                nn.Conv2d(16, 32, 3), nn.ReLU(), nn.AdaptiveAvgPool2d((4, 4)))
            self.head = nn.Sequential(nn.Flatten(), nn.Linear(32 * 4 * 4, 64),
                                      nn.ReLU(), nn.Linear(64, 10))
        def forward(self, x):
            return self.head(self.features(x))
    return Net()


def load_dataset(name, root):
    import torchvision
    from torchvision import transforms
    transform = transforms.ToTensor()
    cls = torchvision.datasets.MNIST if name == "mnist" else torchvision.datasets.CIFAR10
    train = cls(root=root, train=True, download=True, transform=transform)
    test = cls(root=root, train=False, download=True, transform=transform)
    return train, test


def local_train(global_state, template, dataset, indices, cfg, method, device, seed):
    import torch
    from torch.utils.data import DataLoader, Subset
    torch.manual_seed(seed)
    local = copy.deepcopy(template).to(device)
    local.load_state_dict(global_state)
    local.train()
    reference = [p.detach().clone() for p in local.parameters()]
    opt = torch.optim.Adam(local.parameters(), lr=cfg["learning_rate"])
    loader = DataLoader(Subset(dataset, indices.tolist()), batch_size=cfg["batch_size"],
                        shuffle=True, num_workers=0)
    for _ in range(cfg["local_epochs"]):
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss = torch.nn.functional.cross_entropy(local(x), y)
            if method == "fedprox":
                proximal = sum((param - base).square().sum()
                               for param, base in zip(local.parameters(), reference))
                loss = loss + cfg.get("prox_mu", 0.01) * proximal / 2
            loss.backward()
            opt.step()
    return {key: value.detach().cpu().clone() for key, value in local.state_dict().items()}


def evaluate(template, state, dataset, batch_size, device):
    import torch
    from torch.utils.data import DataLoader
    template.load_state_dict(state)
    template.to(device).eval()
    correct = 0
    with torch.no_grad():
        for x, y in DataLoader(dataset, batch_size=batch_size, num_workers=0):
            correct += int((template(x.to(device)).argmax(1).cpu() == y).sum())
    return correct / len(dataset)


def simulate(cfg, method, seed, tau):
    import torch
    torch.set_num_threads(int(cfg.get("cpu_threads", 2)))
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    device = torch.device(cfg.get("device", "cpu"))
    dataset, test = load_dataset(cfg["dataset"], cfg.get("dataset_root", "./data"))
    indices_all = np.arange(len(dataset))
    if cfg.get("train_limit"):
        indices_all = indices_all[:int(cfg["train_limit"])]
    labels = np.asarray(dataset.targets).reshape(-1)[indices_all]
    partitions_local = partition_dirichlet(labels, cfg["clients"], cfg["dirichlet_alpha"], seed)
    partitions = [indices_all[p] for p in partitions_local]
    template = model(cfg["dataset"])
    global_state = {k: v.detach().cpu().clone() for k, v in template.state_dict().items()}
    model_bytes = sum(v.numel() * v.element_size() for v in global_state.values())
    count_params = sum(p.numel() for p in template.parameters())
    resource = {"bandwidth": rng.uniform(5, 100, cfg["clients"]),
                "energy": rng.uniform(0.2, 1, cfg["clients"]),
                "accuracy": rng.uniform(0.1, 0.9, cfg["clients"]),
                "latency": rng.uniform(10, 100, cfg["clients"]),
                "compute": rng.uniform(0.5, 2, cfg["clients"])}
    records, edge_cache = [], {}
    last_sync = 0
    for round_index in range(1, cfg["rounds"] + 1):
        start = time.perf_counter()
        eligible = [i for i, partition in enumerate(partitions) if len(partition)]
        if not eligible:
            raise ValueError("All client partitions are empty")
        quantity = min(len(eligible), max(1, math.ceil(cfg["clients"] * cfg["participation_ratio"])))
        if method in ("ahce-fl", "fedcs"):
            rank = score_clients(resource, cfg["selection_weights"])
            selected = sorted(eligible, key=lambda i: (-rank[i], i))[:quantity]
        else:
            selected = rng.choice(eligible, size=quantity, replace=False).tolist()
        by_edge = [[] for _ in range(cfg["edges"])]
        selected_counts = [[] for _ in range(cfg["edges"])]
        client_upload, client_download, round_delay, nonzero = 0, 0, 0.0, 0
        for client in selected:
            base_state = edge_cache.get(client % cfg["edges"], global_state) if method == "ahce-fl" else global_state
            state = local_train(base_state, template, dataset, partitions[client], cfg,
                                method, device, seed + 100000 * round_index + client)
            upload = model_bytes
            if method == "ahce-fl":
                delta = {k: state[k] - base_state[k] for k in state}
                compressed, upload, active = sparsify(delta, tau)
                state = {k: base_state[k] + compressed[k] for k in base_state}
                nonzero += active
            edge = client % cfg["edges"]
            by_edge[edge].append(state)
            selected_counts[edge].append(len(partitions[client]))
            client_upload += upload
            client_download += model_bytes
            round_delay = max(round_delay, 2 * resource["latency"][client] +
                              (upload + model_bytes) * 8 / (resource["bandwidth"][client] * 1e6) * 1000)
        edge_states, edge_counts = [], []
        for groups, counts in zip(by_edge, selected_counts):
            if groups:
                edge_states.append(weighted_state(groups, counts))
                edge_counts.append(sum(counts))
        cloud_upload = 0
        cloud_download = 0
        synced = True
        if method in ("ahce-fl", "hfl"):
            candidate = weighted_state(edge_states, edge_counts)
            divergence = math.sqrt(sum((candidate[k] - global_state[k]).float().square().sum().item()
                                       for k in candidate))
            if method == "ahce-fl":
                for edge_index, groups in enumerate(by_edge):
                    if groups:
                        edge_cache[edge_index] = weighted_state(groups, selected_counts[edge_index])
                synced = should_sync(round_index, last_sync, divergence,
                                     cfg.get("sync_max_gap", 1), cfg.get("sync_threshold", 0.0))
            if synced:
                global_state = candidate
                cloud_upload = len(edge_states) * model_bytes
                cloud_download = len(edge_states) * model_bytes
                last_sync = round_index
                edge_cache.clear()
        else:
            global_state = weighted_state([s for group in by_edge for s in group],
                                          [n for group in selected_counts for n in group])
            cloud_upload = len(selected) * model_bytes
            cloud_download = len(selected) * model_bytes
        accuracy = evaluate(template, global_state, test, cfg["batch_size"], device)
        row = {"round": round_index, "accuracy": accuracy, "participating_clients": len(selected),
               "sync_triggered": int(synced), "parameters": count_params,
               "client_upload_bytes": client_upload, "client_download_bytes": client_download,
               "cloud_upload_bytes": cloud_upload, "cloud_download_bytes": cloud_download,
               "total_bytes": client_upload + client_download + cloud_upload + cloud_download,
               "compressed_entries": nonzero, "modeled_critical_path_ms": round_delay,
               "wall_clock_s": time.perf_counter() - start}
        records.append(row)
        print(json.dumps({"method": method, **row}), flush=True)
    return records


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/smoke.json")
    p.add_argument("--method", choices=("ahce-fl", "fedavg", "fedprox", "fedcs", "hfl"))
    p.add_argument("--seed", type=int)
    p.add_argument("--tau", type=float)
    a = p.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    method = a.method or cfg.get("method", "ahce-fl")
    seed = a.seed if a.seed is not None else cfg["seed"]
    tau = a.tau if a.tau is not None else cfg["compression_threshold"]
    history = simulate(cfg, method, seed, tau)
    folder = Path("results")
    folder.mkdir(exist_ok=True)
    prefix = f"{cfg['dataset']}_{method}_seed{seed}_tau{tau:g}"
    with (folder / (prefix + ".csv")).open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
    (folder / (prefix + ".json")).write_text(json.dumps(
        {"configuration": cfg, "method": method, "seed": seed, "tau": tau,
         "result": history[-1], "measurement_type": "single-process simulation"}, indent=2))
    print("Saved", folder / (prefix + ".csv"))


if __name__ == "__main__":
    main()
