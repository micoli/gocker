import urwid

from gocker.gui.shortcut import Shortcut, shortcuts


class ShortcutHelpStructItem(urwid.WidgetWrap):
    def __init__(self, shortcut: Shortcut):
        self.content = shortcut
        cols = [
            ('fixed', 12, urwid.AttrWrap(
                urwid.Text(' ' + shortcut.key),
                'candidate_sha',
                'candidate_sha_selected'
            )),
            ('fixed', 3, urwid.AttrWrap(
                urwid.Text('B' if shortcut.builtin else 'C'),
                'candidate_sha',
                'candidate_sha_selected'
            )),
            ('fixed', 60, urwid.AttrWrap(
                urwid.Text(shortcut.message.capitalize()),
                'candidate_date',
                'candidate_date_selected'
            ))
        ]
        urwid.WidgetWrap.__init__(self, urwid.Columns(cols, focus_column=1, dividechars=2))

    def selectable(self):
        return True

    def unhandled_input(self, key):
        if key == 'esc':
            urwid.emit_signal(self, 'validated', 'ok')
            return True
        return False


class PopupShortcutsHelp(urwid.WidgetWrap):
    signals = ['validated']

    def __init__(self):  # pylint: disable=super-init-not-called
        self.shortcuts_list_view = urwid.SimpleFocusListWalker([])

        while len(self.shortcuts_list_view) > 0:
            self.shortcuts_list_view.pop()

        self.shortcuts_list_view.extend(
            list(map(
                ShortcutHelpStructItem,
                shortcuts.values()
            ))
        )

        self.__super.__init__(urwid.Frame(
            body=urwid.LineBox(urwid.ListBox(self.shortcuts_list_view), title='Shortcuts'),
            footer=urwid.GridFlow([urwid.Button('Ok', self.validated)], 8, 1, 1, 'center'),
            focus_part='footer'
        ))

    def validated(self, _):
        urwid.emit_signal(self, 'validated', 'ok')

    # pylint: disable=unused-argument
    def unhandled_input(self, key):
        return False
