import datetime
import logging
import pprint
import time
from threading import RLock

import docker
from dependency_injector.wiring import inject, Provide
from event_bus import EventBus

from gocker.gui.dependency_injection import Container
from gocker.gui.events import ContainerMetricsEvent, ContainerLifecycleEvent, ContainerCreatedEvent, \
    ContainerStoppedEvent
from gocker.gui.services.docker_container.docker_containers_metrics import DockerContainerMetricsThread
from gocker.threads import StoppableThread

pp = pprint.PrettyPrinter(indent=4)

epoch = datetime.datetime.utcfromtimestamp(0)


class DockerContainerService:
    def __init__(self):
        self.docker_list_thread = None

    def start(self):
        self.docker_list_thread = DockerListThread()
        self.docker_list_thread.start()

    def update(self):
        self.docker_list_thread.update()

    def stop(self):
        self.docker_list_thread.stop()


class DockerListThread(StoppableThread):
    @inject
    def __init__(
            self,
            docker_client: docker.APIClient = Provide[Container.docker_client],
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name=self.__class__.__name__)
        self.docker_client = docker_client
        self.bus = bus
        self.lock = draw_lock
        self.containers = {}
        self.container_plugins = {}
        self.docker_metrics_collector_thread = DockerMetricsCollectorThread(self)
        self.docker_metrics_collector_thread.start()

    def stop(self):
        self.docker_metrics_collector_thread.stop()
        with self.lock:
            for _, container in self.containers.items():
                container.stop()
        StoppableThread.stop(self)

    def run(self):
        while not self.is_stopped():
            if not self.update():
                return
            time.sleep(1.5)

    def update(self):
        if self.is_stopped():
            return False
        with self.lock:
            containers = list(self.docker_client.containers(False))
            running_container_ids = []
            for container in containers:
                container_id = container['Id']
                container_name = container['Names'][0][1:]
                running_container_ids.append(container_id)
                if container_id not in self.containers:
                    self.__add_container(container, container_id, container_name)
                if container_id in self.containers:
                    self.__update_container(container, container_id)

            for container_id in list(self.containers):
                if container_id not in running_container_ids:
                    self.__del_container(container_id, self.containers[container_id])

        return True

    def __add_container(self, container, container_id, container_name):
        self.containers[container_id] = DockerContainerMetricsThread(
            self,
            container_id,
            container_name,
            container['Ports'],
            container['Labels'],
        )
        self.containers[container_id].start()
        self.bus.emit(ContainerLifecycleEvent.__name__, ContainerLifecycleEvent('start', container_name))
        self.bus.emit(ContainerCreatedEvent.__name__, ContainerCreatedEvent(container_id, container_name, container))

    def __update_container(self, container, container_id):
        self.containers[container_id].metrics.status = container['Status']

    def __del_container(self, container_id, container_name):
        if container_id not in self.containers:
            logging.debug('__del_container %s not in self.containers' % container_id)
            return
        self.containers[container_id].stop()
        self.bus.emit(ContainerLifecycleEvent.__name__, ContainerLifecycleEvent('stop', container_name))
        self.bus.emit(ContainerStoppedEvent.__name__, ContainerStoppedEvent(
            container_id,
            container_name,
            self.containers[container_id].metrics.container_labels
        ))
        del self.containers[container_id]


class DockerMetricsCollectorThread(StoppableThread):
    @inject
    def __init__(
            self,
            docker_list_thread: DockerListThread,
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name=self.__class__.__name__)
        self.bus = bus
        self.draw_lock = draw_lock
        self.docker_list_thread = docker_list_thread

    def run(self):
        while not self.is_stopped():
            with self.draw_lock:
                result = []
                for container_id in self.docker_list_thread.containers:
                    if self.docker_list_thread.containers[container_id].get_container_metrics() is not None:
                        result.append(self.docker_list_thread.containers[container_id].get_container_metrics())
                self.bus.emit(ContainerMetricsEvent.__name__, ContainerMetricsEvent(list(result)))
            time.sleep(1)
