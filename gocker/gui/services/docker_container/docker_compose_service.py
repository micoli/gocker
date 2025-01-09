import logging
import os
import shutil
from threading import RLock
from typing import List

import docker
import yaml
from dependency_injector.wiring import Provide, inject
from event_bus import EventBus
from yaml.loader import SafeLoader

from gocker.gui.bus import set_listeners, listener
from gocker.gui.commands import ComposeServiceActionCommand
from gocker.gui.dependency_injection import Container
from gocker.gui.events import ContainerCreatedEvent, DockerComposeProjectUpdatedEvent, ContainerStoppedEvent
from gocker.gui.services.docker_container.dataclass import DockerComposeProject
from gocker.process import process_exec_detached


class DockerComposeService:
    @inject
    def __init__(
            self,
            docker_client: docker.APIClient = Provide[Container.docker_client],
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        self.bus = bus
        self.docker_client = docker_client
        self.draw_lock = draw_lock
        self.docker_compose_projects: List[DockerComposeProject] = []
        self.docker_compose_services_in_config_file: dict[str:list[str]] = {}
        set_listeners(self, self.bus)

    @listener
    def on_compose_service_action_command(self, command: ComposeServiceActionCommand):
        arguments = [shutil.which('docker'), 'compose']
        for config_file in command.compose_project.config_files:
            arguments.append('-f')
            arguments.append(config_file)
        arguments.append(command.action)
        arguments.append(command.service_name)
        process_exec_detached(arguments, command.compose_project.working_dir)

    @listener
    def on_stopped_container_event(self, event: ContainerStoppedEvent):
        logging.debug(event.container_labels)
        labels = event.container_labels
        if 'com.docker.compose.service' not in labels:
            logging.error(labels)
            return
        if 'com.docker.compose.project' not in labels:
            return

        for index, docker_compose_project in enumerate(self.docker_compose_projects):
            if docker_compose_project.working_dir == labels['com.docker.compose.project.working_dir']:
                service_name = labels['com.docker.compose.service']
                if service_name in docker_compose_project.running_services:
                    docker_compose_project.running_services.remove(service_name)
                    self.docker_compose_projects[index] = docker_compose_project
                    self.bus.emit(
                        DockerComposeProjectUpdatedEvent.__name__,
                        DockerComposeProjectUpdatedEvent(docker_compose_project)
                    )

    @listener
    def on_created_container_event(self, event: ContainerCreatedEvent):
        labels = event.container['Labels']
        if 'com.docker.compose.service' not in labels:
            logging.error(labels)
            return
        if 'com.docker.compose.project' not in labels:
            return

        config_files = self.resolve_full_config_filenames(
            labels['com.docker.compose.project.working_dir'],
            labels['com.docker.compose.project.config_files'].split(','),
        )
        if len(config_files) == 0:
            return
        for config_file in config_files:
            self.read_docker_compose_config_file(config_file)

        is_existing = False
        for docker_compose_project in self.docker_compose_projects:
            if docker_compose_project.working_dir == labels['com.docker.compose.project.working_dir']:
                is_existing = True
                docker_compose_project.running_services.append(labels['com.docker.compose.service'])
                self.bus.emit(
                    DockerComposeProjectUpdatedEvent.__name__,
                    DockerComposeProjectUpdatedEvent(docker_compose_project)
                )
        if not is_existing:
            docker_compose_project = DockerComposeProject(
                '%s-%s' % (labels['com.docker.compose.project.working_dir'], labels['com.docker.compose.project']),
                labels['com.docker.compose.project'],
                config_files,
                labels['com.docker.compose.project.working_dir'],
                [labels['com.docker.compose.service']],
                self.docker_compose_services_in_config_file[config_files[0]],
            )
            self.bus.emit(
                DockerComposeProjectUpdatedEvent.__name__,
                DockerComposeProjectUpdatedEvent(docker_compose_project)
            )
            self.docker_compose_projects.append(docker_compose_project)

    def read_docker_compose_config_file(self, config_file):
        if config_file in self.docker_compose_services_in_config_file:
            return
        try:
            with open(config_file, encoding='utf-8') as file_handler:
                data = yaml.load(file_handler, Loader=SafeLoader)
                if 'services' in data:
                    self.docker_compose_services_in_config_file[config_file] = [
                        service_name for index, service_name in enumerate(data['services'])
                    ]
        except FileNotFoundError:
            logging.exception('Config file not found %s ' % config_file)

    def resolve_full_config_filenames(self, working_dir: str, config_files: List[str]) -> List[str]:
        return list(filter(
            lambda filename: filename is not None,
            map(
                lambda filename: self.resolve_full_config_filename(working_dir, filename),
                config_files
            )
        ))

    @staticmethod
    def resolve_full_config_filename(working_dir: str, config_file: str):

        if os.path.exists(config_file):
            return config_file

        if os.path.exists('%s/%s' % (working_dir, config_file)):
            return '%s/%s' % (working_dir, config_file)

        logging.error('Can not resolve docker-compose filename %s in %s' % (config_file, working_dir))
        return None
