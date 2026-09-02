# Urban Environmental Sensor Risk Monitoring System

**城市环境传感器风险监测系统**

A unified data-engineering project that detects device latency anomalies, evaluates
air-quality risk, and links abnormal monitoring locations to nearby text events.
It combines MapReduce aggregation, Spark RDD/DataFrame processing, and a spatial-text
similarity join behind one reproducible reference pipeline.

## Why this project

Operational sensor data rarely fails in only one dimension. A high-risk reading may
coincide with unstable device latency or a nearby real-world event. This repository
organises three complementary analyses into a single portfolio-ready system:

1. **Latency stability** - compare device/date latency with the device's long-term average.
2. **Air-quality risk** - aggregate CO2, VOC, and PM2.5 scores by device and date.
3. **Spatial-text correlation** - combine geographic distance with Jaccard similarity.

The implementation is original and uses synthetic sample data. It does not include
course handouts, official test data, marking scripts, or private submission files.

## Architecture

| Stage | Distributed API | Output |
|---|---|---|
| Latency anomaly detection | MRJob / Hadoop MapReduce | Device-date latency increases |
| Air-quality risk | Spark RDD and Spark DataFrame | Ranked devices and risky dates |
| Spatial-text matching | Spark RDD | Monitoring-point/event matches |
| Reference pipeline | Python standard library | Consolidated JSON report |

See [docs/architecture.md](docs/architecture.md) for processing details.

## Quick start

The reference pipeline requires only Python 3.10+.

```bash
python -m pip install -e .
sensor-analytics all
```

The command writes `output/report.json` and prints the same report to the terminal.

Individual stages:

```bash
sensor-analytics latency data/samples/latency.csv --threshold 20
sensor-analytics risk data/samples/air_quality.csv --threshold 2
sensor-analytics join data/samples/locations_a.txt data/samples/locations_b.txt \
  --distance 2 --similarity 0.5
```

## Distributed jobs

Install the optional runtime dependencies:

```bash
python -m pip install -r requirements-distributed.txt
```

Run MapReduce locally through MRJob:

```bash
python distributed/mapreduce_latency.py data/samples/latency.csv \
  --threshold 20 -r inline
```

Run the Spark jobs:

```bash
spark-submit distributed/spark_risk_rdd.py \
  data/samples/air_quality.csv output/risk-rdd 2

spark-submit distributed/spark_risk_dataframe.py \
  data/samples/air_quality.csv output/risk-dataframe 2

spark-submit distributed/spark_spatial_text_join.py \
  data/samples/locations_a.txt data/samples/locations_b.txt \
  output/spatial-text 2 0.5
```

## Test

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the tests and the full sample pipeline on every push and pull request.

## Repository layout

```text
data/samples/                  synthetic input data
distributed/                   MRJob and Spark implementations
docs/                          architecture notes
src/urban_sensor_analytics/    dependency-free reference pipeline and CLI
tests/                         unit tests for parsing and all three analyses
```

## License

MIT
