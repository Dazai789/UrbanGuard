import math
import tempfile
import unittest
from pathlib import Path

from urban_sensor_analytics.models import parse_air_reading, parse_spatial_record
from urban_sensor_analytics.reference import air_quality_risk, latency_anomalies, spatial_text_matches
from urban_sensor_analytics.visualization import write_dashboard


class ReferencePipelineTests(unittest.TestCase):
    def test_latency_anomaly_uses_device_overall_average(self):
        rows = [
            "2024-01-01,DEV_1,10",
            "2024-01-01,DEV_1,20",
            "2024-01-02,DEV_1,100",
        ]
        result = latency_anomalies(rows, 20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["日期"], "2024-01-02")
        self.assertAlmostEqual(result[0]["延迟增幅（毫秒）"], 56.6666666667)

    def test_air_risk_ignores_invalid_rows_and_groups_dates(self):
        rows = [
            "1/4/23 14:51,DEV_21,624.8,149.7,12.48",
            "1/4/23 15:25,DEV_21,600.2,162.3,18.13",
            "invalid,row,that,is,ignored",
        ]
        result = air_quality_risk(rows, 2.0)
        self.assertEqual(result[0]["设备编号"], "DEV_21")
        self.assertEqual(result[0]["高风险日期数"], 1)
        self.assertAlmostEqual(result[0]["高风险日期"][0]["平均风险值"], 2.1528333333)

    def test_spatial_join_applies_both_thresholds(self):
        left = ["A0#(1,1)#apple banana orange", "A1#(10,10)#grape kiwi pear"]
        right = ["B0#(1,2)#apple banana grape", "B1#(11,11)#kiwi pear mango"]
        result = spatial_text_matches(left, right, 2.0, 0.5)
        self.assertEqual(
            [(row["监测点编号"], row["事件编号"]) for row in result],
            [("A0", "B0"), ("A1", "B1")],
        )
        self.assertTrue(math.isclose(result[0]["空间距离"], 1.0))

    def test_parsers_validate_and_normalise(self):
        air = parse_air_reading("1/9/23 12:15,DEV_22,619.5,164.3,55.44")
        self.assertEqual(air.date, "1/9/23")
        record = parse_spatial_record("A3#(1.5, -2)#Foo foo BAR")
        self.assertEqual(record.terms, frozenset({"foo", "bar"}))

    def test_dashboard_contains_chinese_sections(self):
        report = {
            "延迟异常": [{"设备编号": "DEV_1", "日期": "2024-01-02", "延迟增幅（毫秒）": 30}],
            "空气质量风险": [{"设备编号": "DEV_2", "高风险日期数": 1, "高风险日期": []}],
            "空间文本匹配": [{"监测点编号": "A0", "事件编号": "B0", "空间距离": 1.0, "杰卡德相似度": 0.5}],
        }
        with tempfile.TemporaryDirectory() as directory:
            dashboard = Path(directory) / "仪表板.html"
            preview = Path(directory) / "预览.svg"
            write_dashboard(report, dashboard, preview)
            self.assertIn("城市环境传感器风险监测仪表板", dashboard.read_text(encoding="utf-8"))
            self.assertIn("延迟异常记录", preview.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
