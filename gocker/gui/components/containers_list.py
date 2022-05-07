import logging
import re
from typing import List

import urwid
from dependency_injector.wiring import Provide
from event_bus import EventBus

from gocker.data_structure.circular_list import CircularList
from gocker.gui.actions import ContainerActions
from gocker.gui.commands import ContainerActionCommand
from gocker.gui.dependency_injection import Container
from gocker.gui.helpers.colored_name import register_by_name
from gocker.gui.services.docker_container.dataclass import DockerContainerMetric
from gocker.gui.shortcut import shortcuts


class ContainersListViewHeader(urwid.WidgetWrap):
    def __init__(
            self,
            sort_column,
            sort_order_desc,
    ):
        sort_order_text = '🔻' if sort_order_desc else '🔺'
        container_header = 'Containers %s' % sort_order_text if sort_column == 'container_name' else 'Containers'
        cpu_header = '%s CPU' % sort_order_text if sort_column == 'cpu_percentage' else 'CPU'
        memory_header = '%s Memory' % sort_order_text if sort_column == 'memory_usage' else 'Memory'
        cols = [
            ('fixed', 40, urwid.Text(container_header)),
            ('fixed', 3, urwid.Text('L')),
            ('fixed', 8, urwid.Text(cpu_header, align=urwid.RIGHT)),
            ('fixed', 3, urwid.Text(' ')),
            ('fixed', 20, urwid.Text(memory_header, align=urwid.RIGHT)),
            ('fixed', 3, urwid.Text(' ')),
            ('fixed', 25, urwid.Text('Status')),
            ('weight', 60, urwid.Text('Ports'))
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=0, dividechars=2))


class ContainersListViewItem(urwid.WidgetWrap):
    def __init__(
            self,
            container_metrics: DockerContainerMetric,
            is_logged: bool,
            is_tagged: bool,
            bus: EventBus = Provide[Container.bus],
    ):
        self.bus = bus
        self.container_metrics = container_metrics
        cols = [
            ('fixed', 40, urwid.AttrWrap(
                urwid.Text(container_metrics.container_name),
                urwid.AttrSpec(
                    '#%s%s' % (
                        register_by_name(container_metrics.container_name), ',bold,underline' if is_tagged else ''),
                    '#000000',
                    256
                ),
                urwid.AttrSpec('#000000%s' % (',bold,underline' if is_tagged else ''), '#c4a000', 256)
            )),
            ('fixed', 3, urwid.AttrWrap(
                urwid.Text('📖' if is_logged else ' '),
                'container_name',
                'container_name_selected'
            )),
            ('fixed', 8, urwid.AttrWrap(
                urwid.Text('{:>5.2f} %'.format(
                    container_metrics.cpu_percentage) if container_metrics.cpu_percentage is not None else '-'),
                'container_cpu_percentage',
                'container_cpu_percentage_selected'
            )),
            ('fixed', 3,
             self.get_trend(container_metrics.cpu_percentage, container_metrics.cpu_percentage_previous)),
            ('fixed', 20, urwid.AttrWrap(
                urwid.Text('{:>20,d}'
                           .format(container_metrics.memory_usage)
                           .replace(',', ' ') if container_metrics.memory_usage is not None else '-'),
                'container_memory_usage',
                'container_memory_usage_selected'
            )),
            ('fixed', 3, self.get_trend(container_metrics.memory_usage, container_metrics.memory_usage_previous)),
            ('fixed', 25, urwid.AttrWrap(
                urwid.Text(container_metrics.status, wrap='clip'),
                'container_memory_usage',
                'container_memory_usage_selected'
            )),
            ('weight', 60, urwid.AttrWrap(
                urwid.Text(self.format_ports(container_metrics), wrap='clip'),
                'container_memory_usage',
                'container_memory_usage_selected'
            )),
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=0, dividechars=2))

    def format_ports(self, container_stat):
        if container_stat.container_ports is None:
            return '-'
        return ','.join(sorted(map(
            self.format_port,
            container_stat.container_ports
        )))

    @staticmethod
    def format_port(port):
        public_port = ''
        if 'PublicPort' in port:
            public_port = port['PublicPort']
        private_port = ''

        if 'PrivatePort' in port and port['PrivatePort'] == public_port:
            private_port = '='

        if 'PrivatePort' in port and port['PrivatePort'] != public_port:
            private_port = port['PrivatePort']

        return '%s:%s' % (public_port, private_port)

    @staticmethod
    def full_format_port(port):
        ip_address = ''
        if 'IP' in port and port['IP'] != '0.0.0.0' and port['IP'] != '::':
            ip_address = port['IP']
        _type = ''
        if 'Type' in port:
            _type = port['Type'][0:1]
        public_port = ''
        if 'PublicPort' in port:
            public_port = port['PublicPort']
        private_port = ''
        if 'PrivatePort' in port and port['PrivatePort'] == public_port:
            private_port = '='
        if 'PrivatePort' in port and port['PrivatePort'] != public_port:
            private_port = port['PrivatePort']

        return '%s:%s/%s->%s' % (ip_address, public_port, _type, private_port)

    @staticmethod
    def get_trend(current, previous):
        if current is None:
            return urwid.AttrWrap(
                urwid.Text('-'),
                'trend_equal',
                'trend_equal_selected'
            )
        if previous is None:
            return urwid.AttrWrap(
                urwid.Text('-'),
                'trend_equal',
                'trend_equal_selected'
            )
        if current == previous:
            return urwid.AttrWrap(
                urwid.Text('≈'),
                'trend_equal',
                'trend_equal_selected'
            )
        if current < previous:
            return urwid.AttrWrap(
                urwid.Text('∆'),
                'trend_up',
                'trend_up_selected'
            )
        return urwid.AttrWrap(
            urwid.Text('∇'),
            'trend_down',
            'trend_down_selected'
        )

    def selectable(self):
        return self.container_metrics is not None

    def keypress(self, _, key):
        container_name = self.container_metrics.container_name

        if key == shortcuts.get('SHOW_LOG').key:
            self.bus.emit(ContainerActionCommand.__name__, ContainerActionCommand(
                ContainerActions.LOG,
                container_name
            ))
            return None

        if key == shortcuts.get('CONTAINER_SHELL').key:
            self.bus.emit(ContainerActionCommand.__name__, ContainerActionCommand(
                ContainerActions.SHELL,
                container_name
            ))
            return None

        if key == shortcuts.get('KILL_CONTAINER').key:
            self.bus.emit(ContainerActionCommand.__name__, ContainerActionCommand(
                ContainerActions.KILL,
                container_name
            ))
            return None

        if key == shortcuts.get('INSPECT_CONTAINER').key:
            self.bus.emit(ContainerActionCommand.__name__, ContainerActionCommand(
                ContainerActions.INSPECT,
                container_name
            ))
            return None

        if key == shortcuts.get('TAG_CONTAINER').key:
            self.bus.emit(ContainerActionCommand.__name__, ContainerActionCommand(
                ContainerActions.TAG,
                container_name
            ))
            return None

        return key


class ContainersListView(urwid.WidgetWrap):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        urwid.register_signal(self.__class__, ['container_changed'])
        self.walker_header = urwid.SimpleFocusListWalker([])
        self.walker = urwid.SimpleFocusListWalker([])
        self.focus_index = None
        self.search_edit = urwid.Edit('Filter: ', align="left", multiline=False)
        self.filter = None
        self.containers = []
        self.logged_containers = []
        self.tagged_container_name = None
        self.sort_columns = CircularList('container_name', 'cpu_percentage', 'memory_usage')
        self.sort_order_desc = False

        self.frame = urwid.Frame(
            header=self.search_edit,
            body=urwid.Frame(
                header=urwid.BoxAdapter(
                    urwid.ListBox(self.walker_header),
                    height=1
                ),
                body=urwid.ListBox(self.walker),
                focus_part='body'
            ),
            focus_part='body'
        )

        urwid.WidgetWrap.__init__(
            self,
            urwid.AttrMap(self.frame, 'bg')
        )
        self.display_search = False

    def modified(self):
        focus_w, _ = self.walker.get_focus()
        if focus_w is None:
            return
        urwid.emit_signal(self, 'container_changed', focus_w.container_metrics if focus_w is not None else None)

    def keypress(self, size, key):
        if key == '/' and self.frame.get_focus_path()[0] == 'body':
            self.display_search = True
            self.frame.set_focus('header')
            return None

        if key == 'enter' and self.frame.get_focus_path()[0] == 'header':
            self.display_search = False
            if self.search_edit.get_edit_text() == '':
                self.filter = None
            else:
                self.filter = re.compile(self.search_edit.get_edit_text(), re.IGNORECASE)
            self.reload_list()
            self.frame.set_focus('body')
            return None

        if key == 'esc' and self.frame.get_focus_path()[0] == 'header':
            self.display_search = False
            self.filter = None
            self.search_edit.set_edit_text('')
            self.frame.set_focus('body')
            return None

        return self.frame.keypress(size, key)

    def next_sort_column_container(self):
        self.sort_columns.next()
        self.reload_list()

    def previous_sort_column_container(self):
        self.sort_columns.prev()
        self.reload_list()

    def toggle_sort_column_direction_container(self):
        self.sort_order_desc = not self.sort_order_desc
        self.reload_list()

    def set_containers_list(
            self,
            containers: List[DockerContainerMetric],
            logged_containers: List[str],
            tagged_container_name: str,
    ):
        self.logged_containers = logged_containers
        self.tagged_container_name = tagged_container_name
        urwid.disconnect_signal(self.walker, 'modified', self.modified)
        focus, _ = self.walker.get_focus()
        previous_focused_item_name = None if (
                focus is None or focus.container_metrics is None
        ) else focus.container_metrics.container_name
        self.containers = containers

        self.reload_list()

        urwid.connect_signal(self.walker, 'modified', self.modified)

        if previous_focused_item_name is not None:
            index = -1
            for container in self.get_filtered_containers():
                index = index + 1
                if container.container_name == previous_focused_item_name:
                    self.walker.set_focus(index)
                    return
        try:
            self.walker.set_focus(0 if len(self.containers) == 0 else 1)
        except IndexError:
            logging.exception('Focus error %d' % len(self.containers))

    def get_filtered_containers(self):
        containers = sorted(
            self.containers,
            key=lambda containerStat: containerStat.get_column(self.sort_columns.current()),
            reverse=self.sort_order_desc
        )

        if self.filter is None:
            return containers

        return [container for container in containers if self.filter.search(container.container_name)]

    def reload_list(self):
        sort_column = self.sort_columns.current()
        while len(self.walker_header) > 0:
            self.walker_header.pop()
        self.walker_header.extend([ContainersListViewHeader(sort_column, self.sort_order_desc)])

        while len(self.walker) > 0:
            self.walker.pop()
        return self.walker.extend(
            [ContainersListViewItem(
                container,
                container.container_name in self.logged_containers,
                container.container_name == self.tagged_container_name
            ) for container in self.get_filtered_containers()]
        )
