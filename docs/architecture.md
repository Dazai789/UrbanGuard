# Architecture

```text
Latency CSV ----------------> MRJob / local reference ----> latency anomalies
Air-quality CSV -----------> Spark RDD + DataFrame ------> risky device dates
Locations A + Locations B -> Spark spatial-text join ----> related nearby events
                                                              |
                                                              v
                                                    consolidated JSON report
```

## Stage 1: latency stability

Records are aggregated by device and date. The combiner reduces shuffle traffic by
merging local `(sum, count)` pairs before the reducer computes each device's overall
average and flags daily averages that exceed it by a configurable threshold.

## Stage 2: air-quality risk

Each valid reading receives a domain score:

```text
risk = CO2 / 1000 + VOC / 300 + PM2.5 / 15
```

RDD and DataFrame implementations independently aggregate average daily risk and
retain dates containing at least one reading above the risk threshold.

## Stage 3: spatial-text join

Monitoring points and external events are joined only when they satisfy both:

- Euclidean distance at or below the spatial threshold;
- Jaccard term similarity at or above the text threshold.

The local reference implementation is deterministic and dependency-free. It serves
as an executable specification for unit tests and small data. The distributed jobs
preserve the same semantics for Hadoop/Spark environments.

