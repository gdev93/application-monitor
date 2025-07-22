import threading

import docker
import schedule
from .config import DockerMonitorConfig
from telegrambot.sender import send_cpu_alarm, send_memory_alert, send_resource_alert
from datetime import datetime


def _compute_cpu_usage(stats):
    cpu_stats = [cpu_value["cpu_percent_value"] for cpu_value in stats]
    mem_stats = [mem_value["memory_percent_value"] for mem_value in stats]
    cpu = sum(cpu_stats) / len(cpu_stats)
    mem = sum(mem_stats) / len(mem_stats)
    return cpu, mem


def _format_stats_output(decoded_stats):
    """Format decoded stats for console output"""
    output = [f"Container: {decoded_stats.get('container_name', 'Unknown')}",
              f"ID: {decoded_stats.get('container_id', 'Unknown')}", f"CPU: {decoded_stats.get('cpu_percent', 'N/A')}",
              f"Memory: {decoded_stats.get('memory_usage', 'N/A')} / {decoded_stats.get('memory_limit', 'N/A')} ({decoded_stats.get('memory_percent', 'N/A')})"]
    return "\n".join(output)


def _decode_container_stats(stats):
    """Decode and format Docker container stats for better readability"""
    decoded = {'container_id': stats.get('id', 'Unknown')[:12], 'timestamp': stats.get('read', 'Unknown'),
               'container_name': stats.get('name', 'Unknown')}
    # CPU Stats
    cpu_stats = stats.get('cpu_stats', {})
    precpu_stats = stats.get('precpu_stats', {})

    if cpu_stats and precpu_stats:
        cpu_usage = cpu_stats.get('cpu_usage', {})
        precpu_usage = precpu_stats.get('cpu_usage', {})

        cpu_delta = cpu_usage.get('total_usage', 0) - precpu_usage.get('total_usage', 0)
        system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
        online_cpus = cpu_stats.get('online_cpus', 1)

        if system_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100
            decoded['cpu_percent'] = f"{cpu_percent:.2f}%"
            decoded['cpu_percent_value'] = cpu_percent
        else:
            decoded['cpu_percent'] = "0.00%"
            decoded['cpu_percent_value'] = 0

    # Memory Stats
    memory_stats = stats.get('memory_stats', {})
    if memory_stats:
        usage = memory_stats.get('usage', 0)
        limit = memory_stats.get('limit', 0)

        decoded['memory_usage'] = f"{usage / (1024 ** 2):.2f} MB"
        decoded['memory_limit'] = f"{limit / (1024 ** 2):.2f} MB"

        if limit > 0:
            memory_percent = (usage / limit) * 100
            decoded['memory_percent'] = f"{memory_percent:.2f}%"
            decoded['memory_percent_value'] = memory_percent
    return decoded


class DockerMonitor:
    def __init__(self):
        self.config = DockerMonitorConfig()
        self.decoded_stats_per_container = {}
        self._lock = threading.RLock()
        try:
            # Test Docker connection first
            url = f"unix:///{self.config.docker_socket_path}"
            print(f"Trying to connect to Docker at {url}...")
            self.client = docker.DockerClient(base_url=url)
            # Try a simple operation to verify connection
            self.client.ping()
            print("✅ Successfully connected to Docker")
        except Exception as e:
            print(f"❌ Docker connection failed: {e}")
            print("\nTroubleshooting steps:")
            print("1. Make sure Docker Desktop is running")
            print("2. Check if your user has Docker permissions")
            print("3. Try running: docker ps")
            raise

    def _do_monitor(self):
        with self._lock:
            try:
                # Add clear cycle separator with timestamp
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{'=' * 80}")
                print(f"🔄 MONITORING CYCLE - {current_time}")
                print(f"{'=' * 80}")

                containers = self.client.containers.list()
                print(f"📊 Found {len(containers)} containers")

                for container in containers:
                    try:
                        stats = container.stats(stream=False, one_shot=False)
                        # Decode the stats
                        decoded_stats = _decode_container_stats(stats)
                        formatted_output = _format_stats_output(decoded_stats)
                        print(f"📈 Container Stats:")
                        print(formatted_output)
                        print("-" * 50)

                        decoded_stats_per_container = self.decoded_stats_per_container.get(container.name)
                        if not decoded_stats_per_container:
                            self.decoded_stats_per_container[container.name] = {
                                "stats": [decoded_stats],
                                "time": datetime.now()
                            }
                            continue
                        time = datetime.now()
                        last_decoded_stats_time = decoded_stats_per_container["time"]
                        stats = decoded_stats_per_container["stats"]
                        if ((time - last_decoded_stats_time).total_seconds() / 60) >= self.config.analysis_period:
                            cpu, mem = _compute_cpu_usage(stats)
                            if self.config.cpu_alarm_threshold < cpu and self.config.memory_alarm_threshold < mem:
                                send_resource_alert(container.name, str(cpu), str(mem), self.config.cpu_alarm_threshold,
                                                    self.config.memory_alarm_threshold)
                            elif self.config.cpu_alarm_threshold < cpu:
                                send_cpu_alarm(container.name, cpu, self.config.cpu_alarm_threshold)
                            elif self.config.memory_alarm_threshold < mem:
                                send_memory_alert(container.name, mem, self.config.memory_alarm_threshold)
                            self.decoded_stats_per_container[container.name]["stats"] = [decoded_stats]
                            self.decoded_stats_per_container[container.name]["time"] = time
                        else:
                            self.decoded_stats_per_container[container.name]["stats"].append(decoded_stats)
                    except Exception as e:
                        print(f"⚠️  Error getting stats for {container.name}: {e}")

                # Add cycle completion indicator
                print(f"✅ Cycle completed at {current_time}")
                print(f"{'=' * 80}\n")

            except Exception as e:
                print(f"❌ Error monitoring containers: {e}")

    def get_stats(self):
        with self._lock:
            simple_stats = {}
            for container in self.decoded_stats_per_container:
                stats = self.decoded_stats_per_container[container]["stats"]
                cpu, mem = _compute_cpu_usage(stats)
                simple_stats[container] = {
                    "cpu": cpu,
                    "memory": mem,
                    "cpu_percent": f"{cpu:.2f}%",
                    "memory_percent": f"{mem:.2f}%"
                }
            return simple_stats

    def start_monitoring(self):
        print(f"🚀 Starting monitoring with {self.config.interval} second intervals")
        schedule.every(self.config.interval).seconds.do(self._do_monitor)

        # Run the scheduler in a loop
        try:
            while True:
                schedule.run_pending()
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped by user")
