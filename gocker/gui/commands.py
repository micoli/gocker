from dataclasses import dataclass

from gocker.gui.services.docker_container.dataclass import DockerComposeProject


@dataclass
class SubprocessActionCommand:
    action: str
    container_name: str
    process_type: str
    group_name: str
    process_name: str


@dataclass
class ContainerActionCommand:
    action: str
    container_name: str


@dataclass
class ComposeServiceActionCommand:
    action: str
    compose_project: DockerComposeProject
    service_name: str
