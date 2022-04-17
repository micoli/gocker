import json
from threading import RLock

import docker
from dependency_injector.wiring import Provide, inject
from event_bus import EventBus

from gocker.gui.bus import set_listeners, listener
from gocker.gui.dependency_injection import Container
from gocker.gui.events import LogReceivedEvent, ContainerCreatedEvent
from gocker.gui.services.log_collector import LogsCollector
from gocker.threads import StoppableThread


class DockerLogsCollectorService(LogsCollector):
    @inject
    def __init__(
            self,
            draw_lock: RLock = Provide[Container.draw_lock],
            bus: EventBus = Provide[Container.bus]
    ):
        super().__init__(draw_lock)
        set_listeners(self, bus)

    @listener
    def container_created_event_listener(self, event: ContainerCreatedEvent):
        if 'gocker-log' not in event.container['Labels']:
            return
        if json.loads(event.container['Labels']['gocker-log']):
            self.toggle_log(event.container_name)

    def toggle_log(self, key):
        if self.is_logged(key):
            self.remove_log(key)
            return
        self.add_log(key)

    def add_log(self, key):
        if key in self.log_threads:
            return
        self.log_threads[key] = DockerLogThread(key)
        self.log_threads[key].start()


class DockerLogThread(StoppableThread):
    @inject
    def __init__(
            self,
            container_name,
            docker_client: docker.APIClient = Provide[Container.docker_client],
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name='%s-%s' % (self.__class__.__name__, container_name))
        self.bus = bus
        self.docker_client = docker_client
        self.container_name = container_name
        self.draw_lock = draw_lock

    def run(self):
        previous_chunk = ''
        for log in self.docker_client.logs(self.container_name, stream=True):
            if self.is_stopped():
                return
            with self.draw_lock:
                text = previous_chunk + log.decode('UTF-8').replace('\x1b', '\n')
                for line in text.splitlines(keepends=True):
                    if line[-1] == '\n':
                        self.bus.emit(LogReceivedEvent.__name__, LogReceivedEvent(self.container_name, line.rstrip()))
                    else:
                        previous_chunk = line
