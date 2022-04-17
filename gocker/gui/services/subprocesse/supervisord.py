import json
import logging
import time
from threading import RLock
from xmlrpc.client import ServerProxy

from dependency_injector.wiring import Provide
from event_bus import EventBus

from gocker.gui.actions import SubprocessActions
from gocker.gui.bus import set_listeners, listener
from gocker.gui.dependency_injection import Container
from gocker.gui.events import SubprocessMetricsEvent, ContainerCreatedEvent, \
    ContainerStoppedEvent, SubprocessContainerStoppedEvent
from gocker.threads import StoppableThread


def supervisord_plugin_factory(container_name, container):
    if 'gocker-supervisor' not in container['Labels']:
        return None
    config = json.loads(container['Labels']['gocker-supervisor'])
    return SupervisordStateThread(
        container_name,
        config['host'],
        config['port'],
        config['username'],
        config['password']
    )


class DockerSubprocessesThread(StoppableThread):
    def __init__(
            self,
            bus: EventBus = Provide[Container.bus],
            lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name=self.__class__.__name__)
        self.bus = bus
        self.lock = lock
        self.container_plugins = {}
        set_listeners(self, self.bus)

    def exec_subprocess_command(self, container_name, _type, action, group_name, process_name):
        self.get_subprocess_thread(_type, container_name).exec_command(action, group_name, process_name)

    def get_subprocess_thread(self, _type, container_name):
        container_id = [container_id for container_id in list(self.container_plugins) if
                        self.container_plugins[container_id].container_name == container_name and
                        self.container_plugins[container_id].process_type == _type][0]

        return self.container_plugins[container_id]

    @listener
    def container_created_event_listener(self, event: ContainerCreatedEvent):
        plugin_thread = supervisord_plugin_factory(
            event.container_name,
            event.container
        )
        if plugin_thread is not None:
            logging.debug('%s -%s supervisord created' % (event.container_name, event.container_id))
            self.container_plugins[event.container_id] = plugin_thread
            self.container_plugins[event.container_id].start()

    @listener
    def container_stopped_event_listener(self, event: ContainerStoppedEvent):
        with self.lock:
            if event.container_id in self.container_plugins:
                thread: SupervisordStateThread = self.container_plugins[event.container_id]
                self.bus.emit(SubprocessContainerStoppedEvent.__name__, SubprocessContainerStoppedEvent(
                    thread.container_name,
                    thread.process_type
                ))
                self.container_plugins[event.container_id].stop()
                del self.container_plugins[event.container_id]

    def stop(self):
        with self.lock:
            for _, container in self.container_plugins.items():
                container.stop()
        StoppableThread.stop(self)

    def run(self):
        while not self.is_stopped():
            if not self.__update():
                return
            time.sleep(1.5)

    def __update(self):
        if self.is_stopped():
            return False
        return True


class SupervisordStateThread(StoppableThread):
    def __init__(
            self,
            container_name,
            host,
            port,
            username,
            password,
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        super().__init__(name='%s-%s' % (self.__class__.__name__, container_name))
        self.bus = bus
        self.draw_lock = draw_lock
        self.container_name = container_name
        self.process_type = 'supervisord'
        self.supervisor_client_options = {
            'host': host,
            'port': port,
            'url': 'http://%s:%s@%s:%d' % (username, password, host, port),
            'username': username,
            'password': password
        }
        try:
            self.supervisor_client = ServerProxy(self.supervisor_client_options['url'] + '/RPC2')
        # pylint: disable=broad-except
        except Exception:
            self.supervisor_client = None

    def get_client_options(self):
        return self.supervisor_client_options

    def exec_command(self, action, group_name, process_name):
        logging.debug('exec_command %s-%s-%s' % (action, group_name, process_name))
        if action == SubprocessActions.START:
            self.supervisor_client.supervisor.startProcessGroup(group_name, False)

        if action == SubprocessActions.STOP:
            self.supervisor_client.supervisor.stopProcessGroup(group_name, False)

        if action == SubprocessActions.RESTART:
            self.supervisor_client.supervisor.stopProcessGroup(group_name, True)
            time.sleep(1)
            self.supervisor_client.supervisor.startProcessGroup(group_name, False)

        self.update()

    def run(self):
        while not self.is_stopped():
            try:
                if self.supervisor_client is None:
                    self.supervisor_client = ServerProxy(self.supervisor_client_options['url'] + '/RPC2')
                try:
                    state = self.supervisor_client.supervisor.getState()
                # pylint: disable=broad-except
                except Exception:
                    time.sleep(1)
                    continue
                if state['statecode'] != 1:
                    return

                self.update()

                time.sleep(1)
            # pylint: disable=broad-except
            except Exception:
                logging.exception('Error in supervisord updater', exc_info=True)
                with self.draw_lock:
                    self.bus.emit(SubprocessMetricsEvent.__name__,
                                  SubprocessMetricsEvent(self.container_name, self.process_type, []))
                time.sleep(1)

    def update(self):
        processes = self.supervisor_client.supervisor.getAllProcessInfo()
        with self.draw_lock:
            self.bus.emit(SubprocessMetricsEvent.__name__,
                          SubprocessMetricsEvent(self.container_name, self.process_type, processes))
