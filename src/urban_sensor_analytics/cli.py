from __future__ import annotations

import argparse
import json
from pathlib import Path

from .reference import air_quality_risk, latency_anomalies, run_pipeline, spatial_text_matches, write_report
from .visualization import write_dashboard


def _lines(path: str) -> list[str]:
    return Path(path).read_text(encoding="utf-8").splitlines()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="城市环境传感器风险监测分析管线")
    subparsers = parser.add_subparsers(dest="command", required=True)

    latency = subparsers.add_parser("latency", help="检测设备每日延迟异常")
    latency.add_argument("input", help="延迟数据文件")
    latency.add_argument("--threshold", type=float, default=20.0, help="延迟增幅阈值（毫秒）")

    risk = subparsers.add_parser("risk", help="汇总空气质量高风险日期")
    risk.add_argument("input", help="空气质量数据文件")
    risk.add_argument("--threshold", type=float, default=2.0, help="空气质量风险阈值")

    join = subparsers.add_parser("join", help="执行空间与文本相似度联合匹配")
    join.add_argument("input_a", help="监测点数据文件")
    join.add_argument("input_b", help="周边事件数据文件")
    join.add_argument("--distance", type=float, default=2.0, help="最大空间距离")
    join.add_argument("--similarity", type=float, default=0.5, help="最低文本相似度")

    all_jobs = subparsers.add_parser("all", help="执行三阶段分析并生成中文报告和仪表板")
    all_jobs.add_argument("--data-dir", default="data/samples", help="示例数据目录")
    all_jobs.add_argument("--output", default="output/分析报告.json", help="JSON 报告路径")
    all_jobs.add_argument("--dashboard", default="docs/可视化仪表板.html", help="HTML 仪表板路径")
    all_jobs.add_argument("--preview", default="docs/仪表板预览.svg", help="SVG 预览图路径")
    all_jobs.add_argument("--latency-threshold", type=float, default=20.0, help="延迟增幅阈值")
    all_jobs.add_argument("--risk-threshold", type=float, default=2.0, help="空气质量风险阈值")
    all_jobs.add_argument("--distance", type=float, default=2.0, help="最大空间距离")
    all_jobs.add_argument("--similarity", type=float, default=0.5, help="最低文本相似度")
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
        write_dashboard(result, Path(args.dashboard), Path(args.preview))
        print(f"分析报告已生成：{args.output}")
        print(f"可视化仪表板已生成：{args.dashboard}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
