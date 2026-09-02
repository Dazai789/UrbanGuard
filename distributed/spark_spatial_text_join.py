"""Spark RDD spatial-text join for monitoring locations and nearby events."""

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
            "left_id": left[0],
            "right_id": right[0],
            "distance": distance,
            "jaccard_similarity": similarity,
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
        .sortBy(lambda row: (row["left_id"], row["right_id"]))
        .map(json.dumps)
    )
    result.saveAsTextFile(output_path)
    sc.stop()


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise SystemExit(
            "usage: spark_spatial_text_join.py INPUT_A INPUT_B OUTPUT MAX_DISTANCE MIN_SIMILARITY"
        )
    run(*sys.argv[1:])

