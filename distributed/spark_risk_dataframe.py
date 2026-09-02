"""使用 Spark DataFrame 实现空气质量风险聚合。"""

import sys

from pyspark.sql import SparkSession, functions as F, types as T


SCHEMA = T.StructType(
    [
        T.StructField("timestamp", T.StringType()),
        T.StructField("device_id", T.StringType()),
        T.StructField("co2_ppm", T.DoubleType()),
        T.StructField("voc_ppb", T.DoubleType()),
        T.StructField("pm25_ugm3", T.DoubleType()),
    ]
)


def run(input_path, output_path, threshold):
    spark = SparkSession.builder.appName("urban-sensor-risk-dataframe").getOrCreate()
    threshold = float(threshold)
    readings = spark.read.schema(SCHEMA).option("header", True).csv(input_path)
    valid = readings.dropna().filter(
        (F.col("co2_ppm") >= 0) & (F.col("voc_ppb") >= 0) & (F.col("pm25_ugm3") >= 0)
    )
    scored = valid.withColumn(
        "risk",
        F.col("co2_ppm") / 1000 + F.col("voc_ppb") / 300 + F.col("pm25_ugm3") / 15,
    ).withColumn("date", F.to_date("timestamp", "M/d/yy H:mm"))
    daily = scored.groupBy("device_id", "date").agg(
        F.avg("risk").alias("average_risk"), F.max("risk").alias("maximum_risk")
    )
    risky = daily.filter(F.col("maximum_risk") >= threshold)
    result = risky.groupBy("device_id").agg(
        F.count("date").alias("高风险日期数"),
        F.sort_array(F.collect_list(F.struct("date", "average_risk"))).alias("高风险日期"),
    ).select(
        F.col("device_id").alias("设备编号"), "高风险日期数", "高风险日期"
    ).orderBy(F.desc("高风险日期数"), "设备编号")
    result.write.mode("overwrite").json(output_path)
    spark.stop()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("用法：spark_risk_dataframe.py 输入路径 输出路径 风险阈值")
    run(sys.argv[1], sys.argv[2], sys.argv[3])
