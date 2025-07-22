import os


class StatsConfig:
    def __init__(self):
        self.interval = int(os.getenv('INTERVAL_SECS', 10))
        self.cpu_alarm_threshold = float(os.getenv('CPU_ALARM_THRESHOLD', 0.001))
        self.memory_alarm_threshold = float(os.getenv('MEMORY_ALARM_THRESHOLD', 0.001))
        self.analysis_period = float(os.getenv('ANALYSIS_PERIOD_MIN', 1))