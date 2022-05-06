import json
import logging
import os
import queue
import shutil
from typing import List

from datetime import datetime
from threading import RLock

import docker
import urwid
from dependency_injector.wiring import Provide, inject
from event_bus import EventBus
from pygments import highlight, lexers, formatters

from gocker.gui.actions import ContainerActions, SubprocessActions
from gocker.gui.bus import listener, set_listeners
from gocker.gui.commands import SubprocessActionCommand, ContainerActionCommand
from gocker.gui.components.container_inspect import PopupContainerInspect
from gocker.gui.components.container_log_list import ContainerLogListView
from gocker.gui.components.containers_list import ContainersListView
from gocker.gui.components.event_list import EventListView
from gocker.gui.components.services_tree import ServicesTreeView
from gocker.gui.components.shortcuts_help import PopupShortcutsHelp
from gocker.gui.components.stack import Stack
from gocker.gui.dependency_injection import Container
from gocker.gui.events import LogReceivedEvent, ContainerLifecycleEvent, \
    ContainerMetricsEvent, SubprocessMetricsEvent, SystemEvent
from gocker.gui.helpers.tabular_items import TabularItems
from gocker.gui.services.docker_container.dataclass import DockerContainerMetric
from gocker.gui.services.docker_container.docker_compose_service import DockerComposeService
from gocker.gui.services.docker_container.docker_containers_service import DockerContainerService
from gocker.gui.services.docker_container.docker_events import DockerEventsThread
from gocker.gui.services.docker_container.docker_logs_collector_service import DockerLogsCollectorService
from gocker.gui.services.fs_event.fs_events import FsEventsLogThread
from gocker.gui.services.subprocesse.subprocess_logs_collector_service import SubprocessLogsCollectorService
from gocker.gui.services.subprocesse.supervisord import DockerSubprocessesThread
from gocker.gui.shortcut import shortcuts, shortcut_list_chunks

CLEAR_SCREEN = chr(27) + "[2J"

_palette = {
    ("bg", 'white', 'black'),

    ("window", 'white', 'black'),
    ("window_selected", 'light red', 'black'),

    ("separator", 'brown, bold', 'black'),

    ("trend_equal", 'white', 'black'),
    ("trend_equal_selected", 'white', 'black'),

    ("trend_up", 'light red', 'black'),
    ("trend_up_selected", 'light red', 'black'),

    ("trend_down", 'light green', 'black'),
    ("trend_down_selected", 'light green', 'black'),

    ("container_name", 'brown', 'black'),
    ("container_name_selected", 'black', 'brown'),

    ("container_cpu_percentage", 'brown', 'black'),
    ("container_cpu_percentage_selected", 'black', 'brown'),

    ("container_memory_usage", 'brown', 'black'),
    ("container_memory_usage_selected", 'black', 'brown'),

    ("scroll_line", 'brown', 'black'),
    ("scroll_line_selected", 'black', 'brown'),
}


class MainLoop(urwid.MainLoop):
    @inject
    def __init__(
            self,
            widget,
            palette=(),
            unhandled_input=None,
            pop_ups=False,
            draw_lock: RLock = Provide[Container.draw_lock]
    ):
        super().__init__(widget, palette, unhandled_input=unhandled_input, pop_ups=pop_ups)
        self.draw_lock = draw_lock

    def draw_screen(self, *args, **kwargs):
        with self.draw_lock:
            super().draw_screen(*args, **kwargs)


class App:
    # pylint: disable=too-many-instance-attributes
    @inject
    def __init__(
            self,
            message_queue: queue.Queue = Provide[Container.queue],
            docker_client: docker.APIClient = Provide[Container.docker_client],
            bus: EventBus = Provide[Container.bus],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        self.tagged_container_name = None
        self.palette = _palette

        self.bus: EventBus = bus
        self.draw_lock: RLock = draw_lock
        self.docker_client: docker.APIClient = docker_client

        set_listeners(self, self.bus)

        self.containers_list: List[DockerContainerMetric] = None
        self.selected_container = None

        self.subprocesses_treeview = ServicesTreeView()
        self.container_log_listview = ContainerLogListView()
        self.event_listview = EventListView()

        self.containers_list_view = ContainersListView()
        urwid.connect_signal(self.containers_list_view, 'container_changed', self.__container_changed)

        self.docker_insect_popup = PopupContainerInspect()
        urwid.connect_signal(self.docker_insect_popup, 'validated', self.__show_main_screen)

        self.shortcuts_help_popup = PopupShortcutsHelp()
        urwid.connect_signal(self.shortcuts_help_popup, 'validated', self.__show_main_screen)

        self.container_log_listview_frame = urwid.AttrMap(urwid.LineBox(
            self.container_log_listview,
            title='Logs'
        ), 'window', 'window_selected')
        self.event_listview_frame = urwid.AttrMap(urwid.LineBox(
            self.event_listview,
            title='Events'
        ), 'window', 'window_selected')

        shortcut_columns_count = 6
        shortcut_lists = shortcut_list_chunks(shortcut_columns_count)
        self.frame = urwid.AttrMap(Stack([
            ('fixed', len(shortcut_lists[0]) + 2, urwid.LineBox(
                urwid.Columns([(
                    'weight',
                    1,
                    urwid.Filler(urwid.Text('\n'.join(shortcut_text_list)))
                ) for _, shortcut_text_list in enumerate(shortcut_lists)]),
                title='Gocker'
            )),
            ('weight', 60, urwid.Columns([
                ('weight', 4, urwid.AttrMap(urwid.LineBox(
                    self.containers_list_view,
                    title='Containers'
                ), 'window', 'window_selected')),
                ('weight', 3, urwid.AttrMap(urwid.LineBox(
                    self.subprocesses_treeview,
                    title='Subprocesses'
                ), 'window', 'window_selected'))
            ])),
            ('weight', 40, urwid.Columns([
                ('weight', 7, self.container_log_listview_frame),
                ('weight', 3, self.event_listview_frame)
            ]))
        ]), 'bg')

        self.loop = MainLoop(self.frame, self.palette, unhandled_input=self.unhandled_input, pop_ups=True)

        self.tabular_items = TabularItems(self.frame.original_widget, [
            [1, 0],
            [1, 1],
            [2, 0],
            [2, 1],
        ])

        self.message_queue = message_queue
        self.check_messages(self.loop, None)

        self.docker_container_collector: DockerContainerService = DockerContainerService()
        self.docker_container_collector.start()

        self.docker_events_thread: DockerEventsThread = DockerEventsThread()
        self.docker_events_thread.start()

        self.fsevents_thread: FsEventsLogThread = FsEventsLogThread()
        self.fsevents_thread.start()

        self.docker_subprocesses_thread: DockerSubprocessesThread = DockerSubprocessesThread()
        self.docker_subprocesses_thread.start()

        self.docker_logs: DockerLogsCollectorService = DockerLogsCollectorService()
        self.subprocess_logs: SubprocessLogsCollectorService = SubprocessLogsCollectorService()
        self.docker_compose_collector: DockerComposeService = DockerComposeService()

    def stop(self):
        if self.loop_screen_is_started():
            self.loop.stop()
        self.docker_events_thread.stop()
        self.docker_container_collector.stop()
        self.subprocess_logs.stop()
        self.docker_logs.stop()
        self.docker_events_thread.stop()

    def check_messages(self, loop, *_args):
        loop.set_alarm_in(sec=0.5, callback=self.check_messages)
        try:
            self.message_queue.get_nowait()
        except queue.Empty:
            return

    def __draw_containers_list(self):
        if not self.loop_screen_is_started():
            return
        self.containers_list_view.set_containers_list(
            self.containers_list,
            self.docker_logs.get_logged(),
            self.tagged_container_name,
        )

    def __show_main_screen(self, *kwargs):  # pylint: disable=unused-argument
        self.loop.widget = self.frame
        with self.draw_lock:
            self.loop.draw_screen()

    def loop_screen_is_started(self):
        # pylint: disable=protected-access
        return self.loop.screen._started

    @listener
    def system_event_listener(self, event: SystemEvent):
        with self.draw_lock:
            self.event_listview.add_line(event)

    def __container_changed(self, container_name):
        self.selected_container = container_name

    @listener
    def container_lifecycle_event_listener(self, event: ContainerLifecycleEvent):
        pass

    @listener
    def container_metrics_event_listener(self, event: ContainerMetricsEvent):
        self.containers_list = event.metric_list
        self.__draw_containers_list()

    @listener
    def subprocess_metrics_event_listener(self, event: SubprocessMetricsEvent):
        with self.draw_lock:
            self.subprocesses_treeview.set_container_subprocesses(
                event.container_name,
                event.process_type,
                event.processes,
                self.subprocess_logs.get_logged()
            )

    @listener
    def container_action_command_listener(self, command: ContainerActionCommand):
        if command.action == ContainerActions.LOG:
            with self.draw_lock:
                self.docker_logs.toggle_log(command.container_name)
                self.__draw_containers_list()

        if command.action == ContainerActions.SHELL:
            try:
                exec_command = self.docker_client.exec_create(
                    command.container_name,
                    'sh -c "command -v fish || command -v bash || command -v sh"'
                )
                shell_command = self.docker_client.exec_start(exec_command['Id']).decode("utf-8").strip()
                self.__shell_command(
                    ' '.join([shutil.which('docker'), 'exec', '-it', command.container_name, shell_command]),
                    True
                )
            except docker.errors.APIError as error:
                logging.error('Error %s' % (error))

        if command.action == ContainerActions.KILL:
            self.docker_client.kill(self.docker_client.containers(filters={'name': command.container_name})[0]['Id'])
            self.docker_container_collector.update()
            self.__draw_containers_list()
            self.selected_container = None

        if command.action == ContainerActions.INSPECT:
            if self.loop.widget == self.frame:
                self.__display_docker_inspect()
                return
            self.__show_main_screen()

        if command.action == ContainerActions.TAG:
            if self.tagged_container_name is None:
                self.tagged_container_name = command.container_name
                self.__draw_containers_list()
                return
            if self.tagged_container_name == command.container_name:
                self.tagged_container_name = None
                self.__draw_containers_list()
                return
            self.tagged_container_name = command.container_name
            self.__draw_containers_list()

    @listener
    def subprocess_action_command_listener(self, command: SubprocessActionCommand):
        if command.action == SubprocessActions.LOG:
            subprocess = self.docker_subprocesses_thread.get_subprocess_thread(
                command.process_type,
                command.container_name
            )
            self.subprocess_logs.toggle_log(
                '%s-%s' % (command.container_name, command.group_name),
                subprocess.get_client_options(),
                command.container_name,
                command.group_name
            )
            return
        self.docker_subprocesses_thread.exec_subprocess_command(
            command.container_name,
            command.process_type,
            command.action,
            command.group_name,
            command.process_name
        )

    @listener
    def log_received_event_listener(self, event: LogReceivedEvent):
        with self.draw_lock:
            self.container_log_listview.add_line(event.context, event.line)

    def __shell_command(self, command, wait=True):
        logging.debug('Starting "%s"' % command)
        self.loop.screen.stop()
        print(CLEAR_SCREEN)
        print(command + '\n')
        os.system(command)
        if wait:
            input('---------------\nPress enter to continue')
        self.loop.screen.start(alternate_buffer=True)
        self.loop.screen.clear()
        with self.draw_lock:
            self.__show_main_screen()

    def display_shortcuts_help(self):
        self.loop.widget = urwid.Overlay(
            self.shortcuts_help_popup,
            self.frame,
            align='center', width=('relative', 60),
            valign='middle', height=('relative', 70)
        )

    def __display_docker_inspect(self):
        self.loop.widget = urwid.Overlay(
            self.docker_insect_popup,
            self.frame,
            align='center', width=('relative', 97),
            valign='middle', height=('relative', 97)
        )
        self.docker_insect_popup.display(
            highlight(
                json.dumps(
                    self.docker_client.containers(filters={'name': self.selected_container.container_name})[0],
                    indent=4,
                ),
                lexers.JsonLexer(),
                formatters.TerminalFormatter()
            ).split('\n')
        )

    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    def unhandled_input(self, key):
        if self.loop.widget != self.frame:
            if self.loop.widget.top_w.unhandled_input(key):
                return

        if key == shortcuts.get('QUIT').key:
            raise KeyboardInterrupt

        if key == shortcuts.get('SHOW_SHORTCUTS').key:
            self.display_shortcuts_help()
            return

        if key == shortcuts.get('SHOW_ALL_LOG').key:
            for container_name in [container['Names'][0][1:] for container in self.docker_client.containers(False)]:
                self.docker_logs.add_log(container_name)
            self.__draw_containers_list()
            return

        if key == shortcuts.get('LOG_MARKER').key:
            self.bus.emit(LogReceivedEvent.__name__, LogReceivedEvent(
                '--------------------------',
                datetime.now().strftime("%d/%m/%y %H:%M:%S")
            ))
            return

        if key == shortcuts.get('SELECT_NEXT_SORT_COLUMN').key:
            self.containers_list_view.next_sort_column_container()
            return

        if key == shortcuts.get('SELECT_PREVIOUS_SORT_COLUMN').key:
            self.containers_list_view.previous_sort_column_container()
            return

        if key == shortcuts.get('SELECT_TOGGLE_SORT_ORDER').key:
            self.containers_list_view.toggle_sort_column_direction_container()
            return

        if key == shortcuts.get('SELECT_NEXT_PANE').key:
            self.tabular_items.handle_next()
            return

        if key == shortcuts.get('SELECT_PREVIOUS_PANE').key:
            self.tabular_items.handle_previous()
            return

        return
