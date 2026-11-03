# AHCE-FL reproducibility and revision evidence
All values below come from the stored CIFAR-10 experiment CSV files.
Modeled communication bytes do not represent observed network packets.
Accuracy and communication are reported as separate outcomes.

## Results by configuration
| Study | Setting | Seeds | Final accuracy mean | 95% t CI | Mean cloud sync events | Mean modeled bytes |
|---|---|---:|---:|---|---:|---:|
| baseline | ahce-fl | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |
| baseline | fedavg | 3 | 0.643467 | [0.607108, 0.679825] | 100.00 | 617120000 |
| baseline | fedcs | 3 | 0.509367 | [0.499636, 0.519097] | 100.00 | 617120000 |
| baseline | fedprox | 3 | 0.641533 | [0.610213, 0.672854] | 100.00 | 617120000 |
| baseline | hfl | 3 | 0.642400 | [0.608624, 0.676176] | 100.00 | 450291893 |
| compression | 0 | 3 | 0.505900 | [0.501590, 0.510210] | 100.00 | 442269333 |
| compression | 0.001 | 3 | 0.505900 | [0.501590, 0.510210] | 100.00 | 442269333 |
| compression | 0.01 | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |
| compression | 0.05 | 3 | 0.186133 | [0.091097, 0.281169] | 100.00 | 288659957 |
| original_sync | 1 | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |
| original_sync | 2 | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |
| original_sync | 3 | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |
| original_sync | 5 | 3 | 0.473067 | [0.433701, 0.512432] | 100.00 | 366004619 |

## Paired seed comparisons
Comparisons are exploratory because each group contains only three independent seeds.
| Study | Candidate minus reference | Mean difference | 95% t CI | Two-sided paired p-value |
|---|---|---:|---|---:|
| baseline | fedavg minus ahce-fl | 0.170400 | [0.133304, 0.207496] | 0.0025502375 |
| baseline | fedcs minus ahce-fl | 0.036300 | [0.001813, 0.070787] | 0.0454560047 |
| baseline | fedprox minus ahce-fl | 0.168467 | [0.122400, 0.214533] | 0.0040146996 |
| baseline | hfl minus ahce-fl | 0.169333 | [0.137235, 0.201432] | 0.0019353199 |
| compression | 0.001 minus 0 | 0.000000 | [0.000000, 0.000000] | 1.0000000000 |
| compression | 0.01 minus 0 | -0.032833 | [-0.069861, 0.004194] | 0.0623422335 |
| compression | 0.05 minus 0 | -0.319767 | [-0.411030, -0.228504] | 0.0043711514 |
| original_sync | 2 minus 1 | 0.000000 | [0.000000, 0.000000] | 1.0000000000 |
| original_sync | 3 minus 1 | 0.000000 | [0.000000, 0.000000] | 1.0000000000 |
| original_sync | 5 minus 1 | 0.000000 | [0.000000, 0.000000] | 1.0000000000 |

## Required manuscript corrections
- Remove unsupported AHCE-FL classification-accuracy superiority statements.
- Clarify client-selection proxy factors and the chosen normalized weights.
- Separate compressed-upload payload estimates from physical network measurements.
- State explicitly that no differential privacy or secure aggregation mechanism was experimentally validated.
- The original synchronization gap ablation triggered 100 cloud synchronizations per seed and setting, so it cannot isolate the maximum-gap effect.
- Describe the corrected ablation as a maximum-gap isolation experiment with the divergence trigger disabled by threshold 1e9. It does not establish the effectiveness of adaptive divergence threshold selection.
- Recheck the corrected ablation against its per-round trigger telemetry before making any latency or energy claims.
- Obtain and verify the actual reviewer correspondence and target journal format before preparing the final response and manuscript.
