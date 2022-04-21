from threading import RLock

import urwid
import urwidtrees
from dependency_injector.wiring import inject, Provide
from event_bus import EventBus
from urwidtrees import ArrowTree

from gocker.gui.actions import SubprocessActions, ComposeServiceActions
from gocker.gui.bus import set_listeners, listener
from gocker.gui.commands import SubprocessActionCommand, ComposeServiceActionCommand
from gocker.gui.dependency_injection import Container
from gocker.gui.events import SubprocessContainerStoppedEvent, DockerComposeProjectUpdatedEvent
from gocker.gui.helpers.colored_name import register_by_name
from gocker.gui.services.docker_container.dataclass import DockerComposeProject
from gocker.gui.shortcut import shortcuts


class SimpleArrowTree(ArrowTree):
    def decorate(self, pos, widget, is_first=True):
        """
        builds a list element for given position in the tree.
        It consists of the original widget taken from the Tree and some
        decoration columns depending on the existence of parent and sibling
        positions. The result is a urwid.Columns widget.
        """
        if widget is None:
            return None
        if pos is None:
            return None

        original_widget = widget
        cols = self._construct_spacer(pos, [])

        # Construct arrow leading from parent here,
        # if we have a parent and indentation is turned on
        if self._indent > 0:
            if is_first:
                indent = self._construct_first_indent(pos)
                if indent is not None:
                    cols = cols + indent
            else:
                parent = self._tree.parent_position(pos)
                if self._indent > 0 and parent is not None:
                    parent_sib = self._tree.next_sibling_position(pos)
                    draw_vbar = parent_sib is not None
                    void = urwid.AttrMap(urwid.SolidFill(' '), self._arrow_att)
                    if self._childbar_offset > 0:
                        cols.append((self._childbar_offset, void))
                    if draw_vbar:
                        barw = urwid.SolidFill(self._arrow_vbar_char)
                        _bar = urwid.AttrMap(barw, self._arrow_vbar_att or self._arrow_att)
                        rspace_width = self._indent - 1 - self._childbar_offset
                        cols.append((1, _bar))
                        cols.append((rspace_width, void))
                    else:
                        cols.append((self._indent, void))

        # add the original widget for this line
        cols.append(original_widget)
        # construct a Columns, defining all spacer as Box widgets
        line = urwid.Columns(cols, box_columns=range(len(cols))[:-1])
        return line


class FocusableNode(urwid.WidgetWrap):
    def __init__(self, txt):
        urwid.WidgetWrap.__init__(
            self,
            urwid.AttrMap(
                urwid.Text(txt),
                'scroll_line',
                'scroll_line_selected'
            )
        )

    def selectable(self):
        return True

    @staticmethod
    def keypress(_, key):
        return key


class ContainerNode(urwid.WidgetWrap):
    def __init__(self, container_name):
        self.container_name = container_name
        urwid.WidgetWrap.__init__(
            self,
            urwid.AttrMap(
                urwid.Text(container_name),
                urwid.AttrSpec(
                    '#%s' % register_by_name(container_name),
                    '#000000',
                    256
                ),
                'scroll_line_selected'
            )
        )

    def selectable(self):
        return False

    @staticmethod
    def keypress(_, key):
        return key


class ComposeProjectNode(urwid.WidgetWrap):
    def __init__(self, project_name):
        self.project_name = project_name
        urwid.WidgetWrap.__init__(
            self,
            urwid.AttrMap(
                urwid.Text(project_name),
                'scroll_line'
                'scroll_line_selected'
            )
        )

    def selectable(self):
        return False

    @staticmethod
    def keypress(_, key):
        return key


class ContainerSubprocessNode(urwid.WidgetWrap):
    @inject
    def __init__(
            self,
            container_name: str,
            _type: str,
            subprocess: object,
            is_logged: bool,
            bus: EventBus = Provide[Container.bus]
    ):
        self.container_name = container_name
        self.type = _type
        self.subprocess = subprocess
        self.bus = bus
        cols = [
            ('fixed', 30, urwid.AttrWrap(
                urwid.Text(subprocess['name'], wrap='clip'),
                'scroll_line', 'scroll_line_selected'
            )),
            ('fixed', 3, urwid.AttrWrap(
                urwid.Text('📖' if is_logged else ' '),
                'container_name',
                'container_name_selected'
            )),
            ('fixed', 15, urwid.AttrWrap(
                urwid.Text(subprocess['statename']),
                'scroll_line', 'scroll_line_selected'
            )),
            ('weight', 10, urwid.AttrWrap(
                urwid.Text(subprocess['description']),
                'scroll_line', 'scroll_line_selected'
            )),
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=0, dividechars=2))

    def selectable(self):
        return True

    def keypress(self, _, key):
        if key == shortcuts.get('SUBPROCESS_START_STOP').key:
            self.bus.emit(SubprocessActionCommand.__name__, SubprocessActionCommand(
                SubprocessActions.STOP if self.subprocess['statename'] == 'RUNNING' else SubprocessActions.START,
                self.container_name,
                self.type,
                self.subprocess['group'],
                self.subprocess['name']
            ))
            return None
        if key == shortcuts.get('SUBPROCESS_RESTART').key:
            self.bus.emit(SubprocessActionCommand.__name__, SubprocessActionCommand(
                SubprocessActions.RESTART,
                self.container_name,
                self.type,
                self.subprocess['group'],
                self.subprocess['name']
            ))
            return None
        if key == shortcuts.get('SHOW_LOG').key:
            self.bus.emit(SubprocessActionCommand.__name__, SubprocessActionCommand(
                SubprocessActions.LOG,
                self.container_name,
                self.type,
                self.subprocess['group'],
                self.subprocess['name']
            ))
            return None
        return key


class ComposeProjectServiceNode(urwid.WidgetWrap):
    @inject
    def __init__(
            self,
            compose_project: DockerComposeProject,
            service_name: str,
            bus: EventBus = Provide[Container.bus]
    ):
        self.compose_project = compose_project
        self.service_name = service_name
        self.state = self.service_name in compose_project.running_services
        self.bus = bus
        cols = [
            ('fixed', 30, urwid.AttrWrap(
                urwid.Text(self.service_name, wrap='clip'),
                urwid.AttrSpec(
                    '#%s' % register_by_name(self.service_name),
                    '#000000',
                    256
                ),
                'scroll_line_selected'
            )),
            ('fixed', 3, urwid.AttrWrap(
                urwid.Text(' '),
                'container_name',
                'container_name_selected'
            )),
            ('weight', 10, urwid.AttrWrap(
                urwid.Text('RUNNING' if self.state else 'STOPPED'),
                'scroll_line', 'scroll_line_selected'
            )),
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=0, dividechars=2))

    def selectable(self):
        return True

    def keypress(self, _, key):
        if key == shortcuts.get('COMPOSER_SERVICES_START_STOP').key:
            self.bus.emit(ComposeServiceActionCommand.__name__, ComposeServiceActionCommand(
                ComposeServiceActions.STOP if self.state else ComposeServiceActions.START,
                self.compose_project,
                self.service_name,
            ))
            return None

        return key


class ServicesTreeView(urwid.WidgetWrap):
    # pylint: disable=too-many-instance-attributes
    @inject
    def __init__(
            self,
            bus: EventBus = Provide[Container.bus],
            lock: RLock = Provide[Container.draw_lock]
    ):
        self.lock = lock
        self.bus = bus
        set_listeners(self, self.bus)
        urwid.register_signal(self.__class__, ['container_changed'])

        self.container_subprocesses_nodes = []
        self.container_subprocesses_service_nodes = {}
        self.compose_project_nodes = []
        self.compose_project_service_nodes = {}
        self.tree = urwidtrees.tree.SimpleTree([
            (FocusableNode('Subprocesses'), self.container_subprocesses_nodes),
            (FocusableNode('Docker-Compose Services'), self.compose_project_nodes)
        ])
        self.tree_widget = urwidtrees.widgets.TreeBox(
            SimpleArrowTree(self.tree),
            focus=None
        )
        urwid.WidgetWrap.__init__(self, urwid.AttrMap(self.tree_widget, 'bg'))

    @listener
    def docker_compose_project_updated_event(self, event: DockerComposeProjectUpdatedEvent):
        self.set_compose_services(event.docker_compose_project)

    @listener
    def sub_process_stopped_event(self, event: SubprocessContainerStoppedEvent):
        with self.lock:
            container_key = self.get_container_key(event.container_name, event.process_type)
            if container_key in self.container_subprocesses_service_nodes:
                self.container_subprocesses_service_nodes.pop(container_key)
                self.container_subprocesses_nodes.remove(
                    [node for node in self.container_subprocesses_nodes if
                     node[0].container_name == event.container_name][0]
                )
                self.refresh_tree()

    @staticmethod
    def get_container_key(container_name, _type):
        return '%s-%s' % (container_name, _type)

    def selectable(self):
        return True

    def set_container_subprocesses(self, container_name, _type, subprocesses, logged_subprocesses):
        with self.lock:
            container_key = self.get_container_key(container_name, _type)
            if container_key in self.container_subprocesses_service_nodes:
                subprocesses_dict = {subprocess['name']: subprocess for subprocess in subprocesses}
                for index, sub_process_node in enumerate(self.container_subprocesses_service_nodes[container_key]):
                    self.container_subprocesses_service_nodes[container_key][index] = (
                        ContainerSubprocessNode(
                            container_name,
                            _type,
                            subprocesses_dict[sub_process_node[0].subprocess['name']],
                            '%s-%s' % (container_name, sub_process_node[0].subprocess['name']) in logged_subprocesses
                        ),
                        None
                    )
                self.refresh_tree()
                return

            self.container_subprocesses_service_nodes[container_key] = [
                (ContainerSubprocessNode(
                    container_name,
                    _type,
                    subprocess,
                    '%s-%s' % (container_name, subprocess['name']) in logged_subprocesses
                ), None) for subprocess in subprocesses
            ]
            self.container_subprocesses_nodes.insert(
                self.__find_container_position(container_name),
                (
                    ContainerNode(container_name),
                    self.container_subprocesses_service_nodes[container_key]
                )
            )
            self.refresh_tree()

    def set_compose_services(self, compose_project: DockerComposeProject):
        with self.lock:
            if compose_project.key in self.compose_project_service_nodes:
                for service_name in compose_project.declared_services:
                    index = self.__find_service_position_in_compose(compose_project, service_name)
                    if index is None:
                        self.compose_project_service_nodes[compose_project.key].append((
                            ComposeProjectServiceNode(
                                compose_project,
                                service_name
                            ),
                            None
                        ))
                    if index is not None:
                        self.compose_project_service_nodes[compose_project.key][index] = (
                            ComposeProjectServiceNode(
                                compose_project,
                                service_name
                            ),
                            None
                        )
                self.refresh_tree()
                return

            self.compose_project_service_nodes[compose_project.key] = [
                (ComposeProjectServiceNode(
                    compose_project,
                    service_name
                ), None) for service_name in compose_project.declared_services
            ]
            self.compose_project_nodes.insert(
                self.__find_compose_position(compose_project.project_name),
                (
                    ComposeProjectNode(compose_project.project_name),
                    self.compose_project_service_nodes[compose_project.key]
                )
            )
            self.tree_widget.refresh()

    def __find_container_position(self, container_name):
        if len(self.container_subprocesses_nodes) == 0:
            return 0
        for index, _tuple in enumerate(self.container_subprocesses_nodes):
            if container_name < _tuple[0].container_name:
                return index

        return len(self.container_subprocesses_nodes)

    def __find_compose_position(self, project_name):
        if len(self.compose_project_nodes) == 0:
            return 0
        for index, _tuple in enumerate(self.compose_project_nodes):
            if project_name < _tuple[0].project_name:
                return index

        return len(self.compose_project_nodes)

    def __find_service_position_in_compose(self, compose_project, service_name):
        if len(self.compose_project_service_nodes[compose_project.key]) == 0:
            return None
        for index, _tuple in enumerate(self.compose_project_service_nodes[compose_project.key]):
            if service_name == _tuple[0].service_name:
                return index
        return None

    def refresh_tree(self):
        #pylint: disable=protected-access
        self.tree_widget._walker.clear_cache()
