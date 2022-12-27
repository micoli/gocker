import json
from threading import RLock

import requests
from dependency_injector.wiring import Provide
from event_bus import EventBus

from gocker.gui.dependency_injection import Container
from gocker.gui.events import SystemEvent
from gocker.threads import StoppableThread


class FsEventsLogThread(StoppableThread):
    def __init__(
            self,
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
            fsevents_address: str = Provide[Container.config.fsevents.address],
            fsevents_port: str = Provide[Container.config.fsevents.port],
    ):
        super().__init__(name=self.__class__.__name__)
        self.bus = bus
        self.draw_lock = draw_lock
        self.fsevents_port = fsevents_port
        self.fsevents_address = fsevents_address

    def run(self):
        if self.fsevents_port == 0:
            return
        request = requests.get(
            'http://%s:%s/logs' % (self.fsevents_address, self.fsevents_port),
            stream=True,
            timeout=30)
        if request.encoding is None:
            request.encoding = 'utf-8'
        try:
            for event in request.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    return
                decoded_event = json.loads(event)
                with self.draw_lock:
                    self.bus.emit(SystemEvent.__name__, SystemEvent(
                        decoded_event['timestamp'],
                        'fs-event',
                        decoded_event['message']
                    ))
        except requests.ConnectionError:
            return
