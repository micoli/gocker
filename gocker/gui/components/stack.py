import urwid


class Stack(urwid.Pile):
    def keypress(self, size, key):
        """Pass the keypress to the widget in focus.
        Unhandled 'up' and 'down' keys may cause a focus change."""
        if not self.contents:
            return key

        item_rows = None
        if len(size) == 2:
            item_rows = self.get_item_rows(size, focus=True)

        i = self.focus_position
        if self.selectable():
            tsize = self.get_item_size(size, i, True, item_rows)
            key = self.focus.keypress(tsize, key)
            return key

        return key
