"""使用 Spark RDD 联合匹配监测点与周边事件的空间和文本信息。"""

import json
import math
import re
import sys

from pyspark import SparkConf, SparkContext


PATTERN = re.compile(
    r"^\s*([^#]+)#\(\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)#(.*)$"
)


def parse(line):
    match = PATTERN.match(line)
    if not match:
        return None
    record_id, x, y, terms = match.groups()
    term_set = frozenset(term.lower() for term in terms.split() if term)
    return record_id.strip(), float(x), float(y), term_set


def qualify(pair, max_distance, min_similarity):
    left, right = pair
    distance = math.hypot(left[1] - right[1], left[2] - right[2])
    similarity = len(left[3] & right[3]) / len(left[3] | right[3])
    if distance <= max_distance and similarity >= min_similarity:
        return {
            "监测点编号": left[0],
            "事件编号": right[0],
            "空间距离": distance,
            "杰卡德相似度": similarity,
        }
    return None


def run(input_a, input_b, output_path, max_distance, min_similarity):
    conf = SparkConf().setAppName("urban-sensor-spatial-text-join")
    sc = SparkContext(conf=conf)
    left = sc.textFile(input_a).map(parse).filter(lambda row: row is not None)
    right = sc.textFile(input_b).map(parse).filter(lambda row: row is not None)
    result = (
        left.cartesian(right)
        .map(lambda pair: qualify(pair, float(max_distance), float(min_similarity)))
        .filter(lambda row: row is not None)
        .sortBy(lambda row: (row["监测点编号"], row["事件编号"]))
        .map(lambda row: json.dumps(row, ensure_ascii=False))
    )
    result.saveAsTextFile(output_path)
    sc.stop()


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(
            "用法：spark_spatial_text_join.py 监测点文件 事件文件 输出路径 最大距离 最低相似度"
        )
    run(*sys.argv[1:])
