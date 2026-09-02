"""使用 Spark RDD 实现空气质量风险聚合。"""

import json
import sys

from pyspark import SparkConf, SparkContext


def parse(line):
    from datetime import datetime

    try:
        timestamp, device_id, co2, voc, pm25 = [part.strip() for part in line.split(",")]
        parsed = datetime.strptime(timestamp, "%m/%d/%y %H:%M")
        values = tuple(float(value) for value in (co2, voc, pm25))
        if any(value < 0 for value in values):
            return None
        risk = values[0] / 1000 + values[1] / 300 + values[2] / 15
        date = f"{parsed.month}/{parsed.day}/{str(parsed.year)[2:]}"
        return (device_id, date), (risk, 1, risk)
    except (ValueError, TypeError):
        return None


def run(input_path, output_path, threshold):
    conf = SparkConf().setAppName("urban-sensor-risk-rdd")
    sc = SparkContext(conf=conf)
    threshold = float(threshold)
    parsed = sc.textFile(input_path).map(parse).filter(lambda row: row is not None)
    daily = parsed.reduceByKey(
        lambda left, right: (left[0] + right[0], left[1] + right[1], max(left[2], right[2]))
    )
    risky = daily.filter(lambda row: row[1][2] >= threshold).map(
        lambda row: (row[0][0], (row[0][1], row[1][0] / row[1][1]))
    )
    result = (
        risky.groupByKey()
        .mapValues(lambda dates: sorted(list(dates)))
        .map(lambda row: {
            "设备编号": row[0],
            "高风险日期数": len(row[1]),
            "高风险日期": [{"日期": date, "平均风险值": score} for date, score in row[1]],
        })
        .sortBy(lambda row: (-row["高风险日期数"], row["设备编号"]))
        .map(lambda row: json.dumps(row, ensure_ascii=False))
    )
    result.saveAsTextFile(output_path)
    sc.stop()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("用法：spark_risk_rdd.py 输入路径 输出路径 风险阈值")
    run(sys.argv[1], sys.argv[2], sys.argv[3])
