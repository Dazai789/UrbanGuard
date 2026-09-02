from __future__ import annotations

import argparse
import json
from pathlib import Path

from .reference import air_quality_risk, latency_anomalies, run_pipeline, spatial_text_matches, write_report


def _lines(path: str) -> list[str]:
    return Path(path).read_text(encoding="utf-8").splitlines()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Urban sensor analytics reference pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    latency = subparsers.add_parser("latency", help="Detect device-date latency anomalies")
    latency.add_argument("input")
    latency.add_argument("--threshold", type=float, default=20.0)

    risk = subparsers.add_parser("risk", help="Summarise risky air-quality dates")
    risk.add_argument("input")
    risk.add_argument("--threshold", type=float, default=2.0)

    join = subparsers.add_parser("join", help="Run the spatial-text similarity join")
    join.add_argument("input_a")
    join.add_argument("input_b")
    join.add_argument("--distance", type=float, default=2.0)
    join.add_argument("--similarity", type=float, default=0.5)

    all_jobs = subparsers.add_parser("all", help="Run all three stages and write a JSON report")
    all_jobs.add_argument("--data-dir", default="data/samples")
    all_jobs.add_argument("--output", default="output/report.json")
    all_jobs.add_argument("--latency-threshold", type=float, default=20.0)
    all_jobs.add_argument("--risk-threshold", type=float, default=2.0)
    all_jobs.add_argument("--distance", type=float, default=2.0)
    all_jobs.add_argument("--similarity", type=float, default=0.5)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "latency":
        result = latency_anomalies(_lines(args.input), args.threshold)
    elif args.command == "risk":
        result = air_quality_risk(_lines(args.input), args.threshold)
    elif args.command == "join":
        result = spatial_text_matches(
            _lines(args.input_a), _lines(args.input_b), args.distance, args.similarity
        )
    else:
        data_dir = Path(args.data_dir)
        result = run_pipeline(
            data_dir / "latency.csv",
            data_dir / "air_quality.csv",
            data_dir / "locations_a.txt",
            data_dir / "locations_b.txt",
            args.latency_threshold,
            args.risk_threshold,
            args.distance,
            args.similarity,
        )
        write_report(result, Path(args.output))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

