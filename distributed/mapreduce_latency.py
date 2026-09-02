"""MRJob implementation of device/date latency anomaly detection."""

from collections import defaultdict

from mrjob.job import MRJob
from mrjob.protocol import JSONValueProtocol, RawValueProtocol
from mrjob.step import MRStep


class LatencyAnomalyJob(MRJob):
    INPUT_PROTOCOL = RawValueProtocol
    OUTPUT_PROTOCOL = JSONValueProtocol

    def configure_args(self):
        super().configure_args()
        self.add_passthru_arg("--threshold", type=float, default=20.0)

    def mapper(self, _, line):
        if not line.strip() or line.lower().startswith("date,"):
            return
        try:
            date, device_id, raw_latency = [part.strip() for part in line.split(",")]
            latency = float(raw_latency)
            if not device_id or latency < 0:
                return
        except (ValueError, TypeError):
            return
        yield device_id, [date, latency, 1]

    def combiner(self, device_id, values):
        daily = defaultdict(lambda: [0.0, 0])
        for date, total, count in values:
            daily[date][0] += total
            daily[date][1] += count
        for date, (total, count) in daily.items():
            yield device_id, [date, total, count]

    def reducer(self, device_id, values):
        daily = defaultdict(lambda: [0.0, 0])
        for date, total, count in values:
            daily[date][0] += total
            daily[date][1] += count
        overall_total = sum(total for total, _ in daily.values())
        overall_count = sum(count for _, count in daily.values())
        overall_average = overall_total / overall_count
        for date in sorted(daily, reverse=True):
            total, count = daily[date]
            daily_average = total / count
            increase = daily_average - overall_average
            if increase > self.options.threshold:
                yield None, {
                    "device_id": device_id,
                    "date": date,
                    "daily_average_ms": daily_average,
                    "overall_average_ms": overall_average,
                    "increase_ms": increase,
                }

    def steps(self):
        return [MRStep(mapper=self.mapper, combiner=self.combiner, reducer=self.reducer)]


if __name__ == "__main__":
    LatencyAnomalyJob.run()

