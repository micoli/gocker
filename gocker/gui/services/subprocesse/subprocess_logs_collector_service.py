from threading import RLock

import requests
import urllib3
from dependency_injector.wiring import inject, Provide
from event_bus import EventBus

from gocker.gui.dependency_injection import Container
from gocker.gui.events import LogReceivedEvent
from gocker.gui.services.log_collector import LogsCollector
from gocker.threads import StoppableThread


class SubprocessLogsCollectorService(LogsCollector):
    @inject
    def __init__(self, lock: RLock = Provide[Container.draw_lock]):
        super().__init__(lock)

    def toggle_log(self, key, supervisor_client_options, container_name, group_name):
        if self.is_logged(key):
            self.remove_log(key)
            return
        self.add_log(key, supervisor_client_options, container_name, group_name)

    def add_log(self, key, supervisor_client_options, container_name, group_name):
        if key in self.log_threads:
            return
        self.log_threads[key] = [
            SupervisordSubprocessLogThread(
                supervisor_client_options,
                container_name,
                group_name,
                'stdout'
            ),
            SupervisordSubprocessLogThread(
                supervisor_client_options,
                container_name,
                group_name,
                'stderr'
            )
        ]
        self.log_threads[key][0].start()
        self.log_threads[key][1].start()

    def stop(self):
        for thread_id in list(self.log_threads):
            self.log_threads[thread_id][0].stop()
            self.log_threads[thread_id][1].stop()
            del self.log_threads[thread_id]


class SupervisordSubprocessLogThread(StoppableThread):
    @inject
    def __init__(
            self,
            supervisor_client_options: dict,
            container_name: str,
            group_name: str,
            stream: str,
            bus: EventBus = Provide[Container.bus],
            lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name='%s-%s-%s' % (self.__class__.__name__, container_name, group_name))
        self.bus = bus
        self.supervisor_client_options = supervisor_client_options
        self.lock = lock
        self.container_name = container_name
        self.group_name = group_name
        self.stream = stream
        url = '%s/logtail/%s/%s' % (self.supervisor_client_options['url'], self.group_name, stream)
        self.request = requests.get(url, stream=True, timeout=20)
        if self.request.encoding is None:
            self.request.encoding = 'utf-8'

    def run(self):
        try:
            for line in self.request.iter_lines(decode_unicode=True):
                if self.is_stopped():
                    return
                with self.lock:
                    self.bus.emit(LogReceivedEvent.__name__, LogReceivedEvent(
                        '%s -%s' % (self.container_name, self.group_name),
                        '[%s] %s' % (self.stream, line.rstrip()),
                    ))
        except urllib3.exceptions.ProtocolError:
            return
        except requests.ConnectionError:
            return
