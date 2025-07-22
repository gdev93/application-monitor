import threading
from datetime import datetime
import schedule
from server_monitor.config import ServerMonitorConfig
import psutil

from telegrambot.sender import send_resource_alert, send_cpu_alarm, send_memory_alert


def _compute_stats_usage(cpu_stats: list, mem_stats: list):
    cpu = sum(cpu_stats) / len(cpu_stats)
    mem = sum(mem_stats) / len(mem_stats)
    return cpu, mem


class ServerMonitor:
    def __init__(self):
        self.config = ServerMonitorConfig()
        self.stats_config = self.config.stats_config
        self._last_analysis_time = datetime.now()
        self._lock = threading.RLock()
        psutil.PROCFS_PATH = self.config.proc_path
        self.server_stats = {
            "cpu": [psutil.cpu_percent()],
            "memory": [psutil.virtual_memory().percent]
        }

    def _do_monitor(self):
        with self._lock:
            server_name = self.config.server_name
            time = datetime.now()
            last_decoded_stats_time = self._last_analysis_time
            if ((time - last_decoded_stats_time).total_seconds() / 60) >= self.stats_config.analysis_period:
                cpu, memory = _compute_stats_usage(self.server_stats["cpu"], self.server_stats["memory"])
                cpu_rounded = round(cpu, 2)
                memory_rounded = round(memory, 2)

                print(f"Server {server_name} CPU: {cpu_rounded:.2f}% Memory: {memory_rounded:.2f}%")
                if self.stats_config.cpu_alarm_threshold < cpu_rounded and self.stats_config.memory_alarm_threshold < memory_rounded:
                    send_resource_alert(server_name, f"{cpu_rounded:.2f}%", f"{memory_rounded:.2f}%",
                                        self.stats_config.cpu_alarm_threshold,
                                        self.stats_config.memory_alarm_threshold)
                elif self.stats_config.cpu_alarm_threshold < cpu_rounded:
                    send_cpu_alarm(server_name, cpu_rounded, self.stats_config.cpu_alarm_threshold)
                elif self.stats_config.memory_alarm_threshold < memory_rounded:
                    send_memory_alert(server_name, memory_rounded, self.stats_config.memory_alarm_threshold)
                self.server_stats["cpu"] = []
                self.server_stats["memory"] = []
                self._last_analysis_time = time
            else:
                cpu_computed = psutil.cpu_percent()
                memory_computed = psutil.virtual_memory().percent
                self.server_stats["cpu"].append(cpu_computed)
                self.server_stats["memory"].append(memory_computed)

    def get_stats(self):
        with self._lock:
            return self.server_stats

    def start_monitoring(self):
        print(
            f"🚀 Starting server monitoring {self.config.server_name} with {self.stats_config.interval} second intervals")
        schedule.every(self.stats_config.interval).seconds.do(self._do_monitor)
        try:
            while True:
                schedule.run_pending()
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")