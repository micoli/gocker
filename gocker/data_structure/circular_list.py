class CircularList():
    def __init__(self, *args):
        if not args:
            raise Exception('No args found')
        self.i = 0
        self.lst = args

    def current(self):
        return self.lst[self.i]

    def next(self):
        self.i = (self.i + 1) % len(self.lst)
        return self.current()

    def prev(self):
        self.i = (self.i - 1) % len(self.lst)
        return self.current()
