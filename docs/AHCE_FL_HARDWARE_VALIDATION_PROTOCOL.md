# AHCE-FL physical network validation protocol

Status: designed, NOT executed. No physical energy/radio claims arise from this plan.

## Question

Compare measured link-layer traffic, energy and latency of AHCE-FL against matched full-update FedAvg-like transport and hierarchical every-round transport, controlling client partitions and observed accuracy. Archive results regardless of direction.

## Physical setup

- One cloud coordinator, one or more physical edge gateways and independent client compute devices; document exact hardware, firmware, wireless stack, PHY/MAC, MTU, fragmentation, clock sync and radio power.
- To claim real federated training, each client must execute local learning and exchange real model updates. M3/nRF52840 sensor motes cannot reasonably execute the manuscript CNN with five local epochs; a mote-based packet replay is a distinct networking experiment, not complete training validation.
- If fewer than 50 clients are deployed, label the topology a scaled proof of implementation rather than validation of the 50-client simulation.
- Pre-register stop criteria, instrumentation resolution, pairing, feasibility targets and inference plan before trials.

## Test cases

1. Direct full model updates every round, FedAvg-style transport baseline.
2. HFL aggregation every round, to isolate edge aggregation.
3. AHCE-FL at tau 0.01, divergence threshold 0.05, gap 3.
4. AHCE-FL at tau 0.01, divergence threshold 1e9, gap 3.
5. AHCE-FL at tau 0.01, divergence threshold 1e9, gap 5.
6. AHCE-FL at tau 0.05, divergence threshold 0.05, gap 3 as accuracy stress condition.

## Required telemetry

For every run and round: session/seed, software and firmware hashes, selected clients, participation counts, sample weights, model update checksum, sparse/dense encoding decision, payload size, frame headers, fragments, packets, ACKs/retries, losses, sync reason, cloud and edge transactions, wall-clock latency, per-device energy integration with calibrated voltage/current instrumentation, compute time, and final task accuracy. Include idle-power subtraction method, failed-run disposition and missing-data accounting.

Never substitute modeled CSV bytes for measured on-air traffic or analytical latency for observed timing.

## Scientific safeguards

Start with a single smoke-test trial and integrity verification. Then use paired repeated trials. Three repetitions may inform feasibility but do not automatically support superiority; plan inference sample sizes using pilot variability and targeted interval precision. No scientific parameter or historical result may be changed to manufacture positive effects. Archive original traces and checksums and report all failures.

## Pending prerequisites

Confirm actual testbed availability, number/type of client compute devices, whether the aim is full training or network-only payload replay, radio/energy instruments, and safe power/environment limits. Only after those prerequisites can execution start. Existing IoT-LAB TSCH trials from a separate project cannot be presented as AHCE-FL experimental validation.
