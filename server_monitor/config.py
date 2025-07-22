import os
from pathlib import Path
from stats_config.stats_config import StatsConfig


class ServerMonitorConfig:
    def __init__(self):
        self.stats_config = StatsConfig()
        self.server_name = os.getenv('SERVER_NAME', 'Server')
        self.proc_path = os.getenv('PROC_PATH', '/proc')