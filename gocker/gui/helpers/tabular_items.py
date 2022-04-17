from urwid import WidgetContainerMixin


class TabularItems:
    def __init__(self, parent: WidgetContainerMixin, items):
        self.parent = parent
        self.items = items
        self.parent.set_focus_path(self.items[0])

    def handle_next(self):
        current_focus_path = self.parent.get_focus_path()
        self.parent.set_focus_path(
            self.items[(self.items.index(current_focus_path) + 1) % len(self.items)]
        )

    def handle_previous(self):
        current_focus_path = self.parent.get_focus_path()
        self.parent.set_focus_path(
            self.items[(self.items.index(current_focus_path) - 1) % len(self.items)]
        )
