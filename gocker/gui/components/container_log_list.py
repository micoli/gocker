import re

import urwid

from gocker.gui.helpers.colored_name import register_by_name
from gocker.gui.helpers.urwidhelper import translate_text_for_urwid


class ContainerLogListViewItem(urwid.WidgetWrap):
    def __init__(self, container_name, line):
        self.container_name = container_name
        self.line = line
        color = register_by_name(container_name) if container_name[0:2] != '--' else 'FF0000'
        cols = [
            ('fixed', 20, urwid.AttrWrap(
                urwid.Text(container_name, wrap='clip'),
                urwid.AttrSpec('#%s' % color, '#000000', 256),
                urwid.AttrSpec('#000000', '#c4a000', 256)
            )),
            ('weight', 10, urwid.AttrWrap(
                urwid.Text(translate_text_for_urwid(line)),
                'container_name',
                'container_name_selected'
            )),
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=0, dividechars=2))

    def selectable(self):
        return True

    @staticmethod
    def keypress(_, key):
        return key


class ContainerLogListView(urwid.WidgetWrap):

    def __init__(self):
        self.walker = urwid.SimpleFocusListWalker([])
        self.search_edit = urwid.Edit('Filter: ', align="left", multiline=False)
        self.filter = None
        self.lines = []

        self.frame = urwid.Frame(
            header=self.search_edit,
            body=urwid.ListBox(self.walker),
            focus_part='body'
        )
        urwid.WidgetWrap.__init__(
            self,
            urwid.AttrMap(self.frame, 'bg')
        )
        self.display_search = False

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
            self.__reload_list()
            self.frame.set_focus('body')
            return None

        if key == 'esc' and self.frame.get_focus_path()[0] == 'header':
            self.display_search = False
            self.filter = None
            self.search_edit.set_edit_text('')
            self.frame.set_focus('body')
            return None

        return self.frame.keypress(size, key)

    def add_line(self, container_name, line):
        if len(line) == 0:
            return
        container_log_list_view_item = ContainerLogListViewItem(container_name, line)
        self.lines.append(container_log_list_view_item)
        if self.filter is not None and self.filter.search(container_name + ' ' + line):
            self.walker.extend([container_log_list_view_item])
        if self.filter is None:
            self.walker.extend([container_log_list_view_item])
        self.walker.set_focus(len(self.walker) - 1)

    def __reload_list(self):
        while len(self.walker) > 0:
            self.walker.pop()
        if self.filter is None:
            self.walker.extend(self.lines)
            return
        self.walker.extend([line for line in self.lines if self.filter.search(line.container_name + ' ' + line.line)])
