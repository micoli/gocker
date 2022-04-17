from datetime import datetime

import urwid

from gocker.gui.events import SystemEvent


class EventListViewItem(urwid.WidgetWrap):
    def __init__(self, event: SystemEvent):
        self.content = event
        cols = [
            ('fixed', 8, urwid.AttrWrap(
                urwid.Text('%s' % datetime.fromtimestamp(event.timestamp).strftime('%H:%M:%S')),
                'container_name',
                'container_name_selected'
            )),
            ('weight', 1, urwid.AttrWrap(
                urwid.Text(event.type),
                'container_name',
                'container_name_selected'
            )),
            ('weight', 5, urwid.AttrWrap(
                urwid.Text(event.message),
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


class EventListView(urwid.WidgetWrap):

    def __init__(self):
        self.walker = urwid.SimpleFocusListWalker([])
        urwid.WidgetWrap.__init__(
            self,
            urwid.ListBox(self.walker)
        )
        self.count = 0

    def add_line(self, event: SystemEvent):
        self.walker.extend(
            [EventListViewItem(event)]
        )
        self.count += 1
        self.walker.set_focus(self.count - 1)
