import urwid

from gocker.gui.helpers.scrollview import ScrollView
from gocker.gui.helpers.tabular_items import TabularItems
from gocker.gui.shortcut import shortcuts


class PopupContainerInspect(urwid.WidgetWrap):
    signals = ['validated']

    def __init__(self):  # pylint: disable=super-init-not-called
        self.display_scroll_view = ScrollView()
        self.frame = urwid.AttrMap(urwid.Frame(
            body=urwid.LineBox(self.display_scroll_view, title='Container'),
            footer=urwid.GridFlow([urwid.Button('Ok', self.validated)], 8, 1, 1, 'center'),
            focus_part='footer'
        ), 'bg')
        self.tabular_items = TabularItems(self.frame.original_widget, [
            ['body'],
            ['footer', 0],
        ])
        self.__super.__init__(self.frame)

    def validated(self, _):
        urwid.emit_signal(self, 'validated', 'ok')

    def display(self, lines):
        self.display_scroll_view.set_lines(lines)

    def unhandled_input(self, key):  # pylint: disable=too-many-branches
        if key == 'esc':
            urwid.emit_signal(self, 'validated', 'ok')
            return True

        if key == shortcuts.get('SELECT_NEXT_PANE').key:
            self.tabular_items.handle_next()
            return True

        if key == shortcuts.get('SELECT_PREVIOUS_PANE').key:
            self.tabular_items.handle_previous()
            return True

        return True
