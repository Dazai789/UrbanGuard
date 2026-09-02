from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from io import StringIO


DATE_FORMATS = ("%m/%d/%y", "%Y-%m-%d", "%m/%d/%Y")
TIMESTAMP_FORMATS = (
    "%m/%d/%y %H:%M",
    "%m/%d/%Y %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
)


@dataclass(frozen=True)
class LatencyReading:
    date: str
    device_id: str
    latency_ms: float


@dataclass(frozen=True)
class AirReading:
    date: str
    sort_date: datetime
    device_id: str
    co2_ppm: float
    voc_ppb: float
    pm25_ugm3: float

    @property
    def risk_score(self) -> float:
        return self.co2_ppm / 1000 + self.voc_ppb / 300 + self.pm25_ugm3 / 15


@dataclass(frozen=True)
class SpatialRecord:
    record_id: str
    x: float
    y: float
    terms: frozenset[str]


def _csv_fields(line: str) -> list[str]:
    return next(csv.reader(StringIO(line.strip())))


def parse_date(value: str) -> datetime:
    value = value.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unsupported date: {value}")


def parse_timestamp(value: str) -> datetime:
    value = value.strip()
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unsupported timestamp: {value}")


def parse_latency(line: str) -> LatencyReading:
    fields = _csv_fields(line)
    if len(fields) != 3:
        raise ValueError("latency row must have 3 fields")
    date, device_id, latency = (field.strip() for field in fields)
    parse_date(date)
    value = float(latency)
    if not device_id or value < 0:
        raise ValueError("invalid latency row")
    return LatencyReading(date=date, device_id=device_id, latency_ms=value)


def parse_air_reading(line: str) -> AirReading:
    fields = _csv_fields(line)
    if len(fields) != 5:
        raise ValueError("air-quality row must have 5 fields")
    timestamp, device_id, co2, voc, pm25 = (field.strip() for field in fields)
    parsed = parse_timestamp(timestamp)
    values = tuple(float(value) for value in (co2, voc, pm25))
    if not device_id or any(value < 0 for value in values):
        raise ValueError("invalid air-quality row")
    return AirReading(
        date=f"{parsed.month}/{parsed.day}/{str(parsed.year)[2:]}",
        sort_date=parsed.replace(hour=0, minute=0, second=0, microsecond=0),
        device_id=device_id,
        co2_ppm=values[0],
        voc_ppb=values[1],
        pm25_ugm3=values[2],
    )


SPATIAL_PATTERN = re.compile(
    r"^\s*([^#]+)#\(\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)#(.*)$"
)


def parse_spatial_record(line: str) -> SpatialRecord:
    match = SPATIAL_PATTERN.match(line)
    if not match:
        raise ValueError("invalid spatial record")
    record_id, x, y, raw_terms = match.groups()
    terms = frozenset(term.lower() for term in raw_terms.split() if term)
    if not record_id.strip() or not terms:
        raise ValueError("spatial record requires an id and at least one term")
    return SpatialRecord(record_id.strip(), float(x), float(y), terms)


def numeric_id(record_id: str) -> tuple[str, int, str]:
    match = re.match(r"^(.*?)(\d+)$", record_id)
    if not match:
        return record_id, -1, record_id
    return match.group(1), int(match.group(2)), record_id

