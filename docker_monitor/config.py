import os
from pathlib import Path


class DockerMonitorConfig:
    def __init__(self):
        self.docker_compose_files = os.getenv('DOCKER_COMPOSE_FILES', 'docker-compose.yaml').split(',')
        self.interval = int(os.getenv('INTERVAL_SECS', 10))
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.cpu_alarm_threshold = float(os.getenv('CPU_ALARM_THRESHOLD', 0.001))
        self.memory_alarm_threshold = float(os.getenv('MEMORY_ALARM_THRESHOLD', 0.001))
        default_docker_socket_path = Path.home() / '.docker' / 'run' / 'docker.sock'
        self.docker_socket_path = os.getenv('DOCKER_SOCKET_PATH', default_docker_socket_path)
        self.analysis_period=float(os.getenv('ANALYSIS_PERIOD_MIN', 1))
