from threading import Thread


class LogsCollector:
    def __init__(self, lock):
        self.lock = lock
        self.log_threads = {}

    def stop(self):
        # pylint: disable=unused-variable
        for thread_id, log_thread in self.log_threads.items():
            log_thread.stop()

    def remove_log(self, key):
        if key not in self.log_threads:
            return

        with self.lock:
            if isinstance(self.log_threads[key], Thread):
                self.log_threads[key].stop()
            else:
                self.log_threads[key][0].stop()
                self.log_threads[key][1].stop()
            del self.log_threads[key]

    def get_logged(self):
        return self.log_threads.keys()

    def is_logged(self, key):
        # pylint: disable=consider-iterating-dictionary
        return key in self.log_threads.keys()
