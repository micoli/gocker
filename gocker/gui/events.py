from dataclasses import dataclass
from typing import List

from gocker.gui.services.docker_container.dataclass import DockerComposeProject
from gocker.gui.services.docker_container.dataclass import DockerContainerMetric


@dataclass
class ContainerCreatedEvent:
    container_id: str
    container_name: str
    container: object


@dataclass
class ContainerStoppedEvent:
    container_id: str
    container_name: str
    container_labels: object


@dataclass
class LogReceivedEvent:
    context: str
    line: str


@dataclass
class ContainerLifecycleEvent:
    event: str
    container_name: str


@dataclass
class SystemEvent:
    timestamp: float
    type: str
    message: str


@dataclass
class ContainerMetricsEvent:
    metric_list: List[DockerContainerMetric]


@dataclass
class SubprocessMetricsEvent:
    container_name: str
    process_type: str
    processes: list


@dataclass
class SubprocessContainerStoppedEvent:
    container_name: str
    process_type: str


@dataclass
class DockerComposeProjectUpdatedEvent:
    docker_compose_project: DockerComposeProject
