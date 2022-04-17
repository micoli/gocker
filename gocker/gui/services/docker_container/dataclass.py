from dataclasses import dataclass


@dataclass
class DockerComposeProject:
    key: str
    project_name: str
    config_files: list[str]
    working_dir: str
    running_services: list[str]
    declared_services: list[str]


# pylint: disable=too-many-instance-attributes
@dataclass
class DockerContainerMetric:
    container_id: str
    container_name: str
    container_ports: list
    container_labels: list
    status: str = ''
    time_read: int = 0
    cpu_percentage: float = None
    cpu_percentage_previous: float = None
    memory_usage: int = None
    memory_usage_previous: int = None

    def get_column(self, column_name):
        if column_name == 'container_name':
            return self.container_name
        if column_name == 'cpu_percentage':
            return self.cpu_percentage if self.cpu_percentage is not None else 0
        if column_name == 'memory_usage':
            return self.memory_usage if self.memory_usage is not None else 0
        return None
