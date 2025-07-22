import os
from pathlib import Path

from stats_config.stats_config import StatsConfig


class DockerMonitorConfig:
    def __init__(self):
        default_docker_socket_path = Path.home() / '.docker' / 'run' / 'docker.sock'
        self.docker_socket_path = os.getenv('DOCKER_SOCKET_PATH', default_docker_socket_path)
        self.stats_config = StatsConfig()