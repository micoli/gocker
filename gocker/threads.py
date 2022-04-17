import logging
from threading import Thread, Event


class StoppableThread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        super().__init__(
            group=group,
            target=target,
            name=name,
            args=args,
            kwargs=kwargs,
            daemon=daemon)
        logging.debug('%s Starting ' % self.name)
        self.daemon = True
        self._stop = Event()

    def stop(self):
        logging.debug('%s Stopping ' % self.name)
        self._stop.set()

    def is_stopped(self):
        if self._stop.isSet():
            logging.debug('%s Is stop = TRUE' % self.name)
        return self._stop.isSet()
