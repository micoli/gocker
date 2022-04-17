from threading import RLock

import docker
from dependency_injector.wiring import Provide
from event_bus import EventBus

from gocker.gui.dependency_injection import Container
from gocker.gui.events import SystemEvent
from gocker.threads import StoppableThread


class DockerEventsThread(StoppableThread):
    def __init__(
            self,
            docker_client: docker.APIClient = Provide[Container.docker_client],
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name=self.__class__.__name__)
        self.bus = bus
        self.docker_client = docker_client
        self.draw_lock = draw_lock

    def run(self):
        for event in self.docker_client.events(decode=True):
            if self.is_stopped():
                return
            with self.draw_lock:
                self.bus.emit(SystemEvent.__name__, SystemEvent(
                    event['time'],
                    event['Type'],
                    event['Action']
                ))
