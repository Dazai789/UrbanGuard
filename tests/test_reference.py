import math
import unittest

from urban_sensor_analytics.models import parse_air_reading, parse_spatial_record
from urban_sensor_analytics.reference import air_quality_risk, latency_anomalies, spatial_text_matches


class ReferencePipelineTests(unittest.TestCase):
    def test_latency_anomaly_uses_device_overall_average(self):
        rows = [
            "2024-01-01,DEV_1,10",
            "2024-01-01,DEV_1,20",
            "2024-01-02,DEV_1,100",
        ]
        result = latency_anomalies(rows, 20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2024-01-02")
        self.assertAlmostEqual(result[0]["increase_ms"], 56.6666666667)

    def test_air_risk_ignores_invalid_rows_and_groups_dates(self):
        rows = [
            "1/4/23 14:51,DEV_21,624.8,149.7,12.48",
            "1/4/23 15:25,DEV_21,600.2,162.3,18.13",
            "invalid,row,that,is,ignored",
        ]
        result = air_quality_risk(rows, 2.0)
        self.assertEqual(result[0]["device_id"], "DEV_21")
        self.assertEqual(result[0]["risky_date_count"], 1)
        self.assertAlmostEqual(result[0]["dates"][0]["average_risk"], 2.1528333333)

    def test_spatial_join_applies_both_thresholds(self):
        left = ["A0#(1,1)#apple banana orange", "A1#(10,10)#grape kiwi pear"]
        right = ["B0#(1,2)#apple banana grape", "B1#(11,11)#kiwi pear mango"]
        result = spatial_text_matches(left, right, 2.0, 0.5)
        self.assertEqual([(row["left_id"], row["right_id"]) for row in result], [("A0", "B0"), ("A1", "B1")])
        self.assertTrue(math.isclose(result[0]["distance"], 1.0))

    def test_parsers_validate_and_normalise(self):
        air = parse_air_reading("1/9/23 12:15,DEV_22,619.5,164.3,55.44")
        self.assertEqual(air.date, "1/9/23")
        record = parse_spatial_record("A3#(1.5, -2)#Foo foo BAR")
        self.assertEqual(record.terms, frozenset({"foo", "bar"}))


if __name__ == "__main__":
    unittest.main()

