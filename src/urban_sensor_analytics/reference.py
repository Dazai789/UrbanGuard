from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from .models import (
    AirReading,
    LatencyReading,
    SpatialRecord,
    numeric_id,
    parse_air_reading,
    parse_date,
    parse_latency,
    parse_spatial_record,
)


def _valid_rows(lines: Iterable[str], parser):
    for line in lines:
        if not line.strip() or line.lower().startswith(("date,", "timestamp,")):
            continue
        try:
            yield parser(line)
        except (ValueError, TypeError):
            continue


def latency_anomalies(
    lines: Iterable[str], threshold: float
) -> list[dict[str, float | str]]:
    readings: list[LatencyReading] = list(_valid_rows(lines, parse_latency))
    overall: dict[str, list[float]] = defaultdict(list)
    daily: dict[tuple[str, str], list[float]] = defaultdict(list)
    for reading in readings:
        overall[reading.device_id].append(reading.latency_ms)
        daily[(reading.device_id, reading.date)].append(reading.latency_ms)

    results = []
    for (device_id, date), values in daily.items():
        overall_avg = sum(overall[device_id]) / len(overall[device_id])
        daily_avg = sum(values) / len(values)
        increase = daily_avg - overall_avg
        if increase > threshold:
            results.append(
                {
                    "设备编号": device_id,
                    "日期": date,
                    "当日平均延迟（毫秒）": daily_avg,
                    "设备总体平均延迟（毫秒）": overall_avg,
                    "延迟增幅（毫秒）": increase,
                }
            )
    return sorted(
        results,
        key=lambda row: (row["设备编号"], -parse_date(str(row["日期"])).timestamp()),
    )


def air_quality_risk(
    lines: Iterable[str], threshold: float
) -> list[dict[str, object]]:
    readings: list[AirReading] = list(_valid_rows(lines, parse_air_reading))
    grouped: dict[tuple[str, str], list[AirReading]] = defaultdict(list)
    for reading in readings:
        grouped[(reading.device_id, reading.date)].append(reading)

    devices: dict[str, list[dict[str, object]]] = defaultdict(list)
    for (device_id, date), values in grouped.items():
        scores = [value.risk_score for value in values]
        if any(score >= threshold for score in scores):
            devices[device_id].append(
                {
                    "日期": date,
                    "平均风险值": sum(scores) / len(scores),
                }
            )

    result = []
    for device_id, risky_dates in devices.items():
        risky_dates.sort(key=lambda row: parse_date(str(row["日期"])))
        result.append(
            {
                "设备编号": device_id,
                "高风险日期数": len(risky_dates),
                "高风险日期": risky_dates,
            }
        )
    return sorted(result, key=lambda row: (-int(row["高风险日期数"]), row["设备编号"]))


def spatial_text_matches(
    lines_a: Iterable[str],
    lines_b: Iterable[str],
    max_distance: float,
    min_similarity: float,
) -> list[dict[str, float | str]]:
    records_a: list[SpatialRecord] = list(_valid_rows(lines_a, parse_spatial_record))
    records_b: list[SpatialRecord] = list(_valid_rows(lines_b, parse_spatial_record))
    results = []
    for left in records_a:
        for right in records_b:
            distance = math.hypot(left.x - right.x, left.y - right.y)
            intersection = len(left.terms & right.terms)
            union = len(left.terms | right.terms)
            similarity = intersection / union if union else 0.0
            if distance <= max_distance and similarity >= min_similarity:
                results.append(
                    {
                        "监测点编号": left.record_id,
                        "事件编号": right.record_id,
                        "空间距离": distance,
                        "杰卡德相似度": similarity,
                    }
                )
    return sorted(
        results,
        key=lambda row: (numeric_id(str(row["监测点编号"])), numeric_id(str(row["事件编号"]))),
    )


def run_pipeline(
    latency_path: Path,
    air_path: Path,
    locations_a_path: Path,
    locations_b_path: Path,
    latency_threshold: float,
    risk_threshold: float,
    max_distance: float,
    min_similarity: float,
) -> dict[str, object]:
    return {
        "延迟异常": latency_anomalies(
            latency_path.read_text(encoding="utf-8").splitlines(), latency_threshold
        ),
        "空气质量风险": air_quality_risk(
            air_path.read_text(encoding="utf-8").splitlines(), risk_threshold
        ),
        "空间文本匹配": spatial_text_matches(
            locations_a_path.read_text(encoding="utf-8").splitlines(),
            locations_b_path.read_text(encoding="utf-8").splitlines(),
            max_distance,
            min_similarity,
        ),
    }


def write_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
