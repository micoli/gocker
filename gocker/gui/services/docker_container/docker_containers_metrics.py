import datetime
import pprint
from threading import RLock

import docker
import parsedatetime as pdt
from dependency_injector.wiring import Provide, inject

from gocker.gui.dependency_injection import Container
from gocker.gui.services.docker_container.dataclass import DockerContainerMetric
from gocker.threads import StoppableThread

pp = pprint.PrettyPrinter(indent=4)

date_parser = pdt.Calendar(pdt.Constants())
epoch = datetime.datetime.utcfromtimestamp(0)


def unix_time_millis(_datetime):
    return (_datetime - epoch).total_seconds() * 1000


def parse_date_time(time_str):
    _datetime, _, microseconds = time_str.partition(".")
    _datetime = datetime.datetime.strptime(_datetime, "%Y-%m-%dT%H:%M:%S")
    microseconds = int(microseconds.rstrip("Z"), 10)
    return _datetime + datetime.timedelta(microseconds=microseconds)


class DockerContainerMetricsThread(StoppableThread):
    @inject
    def __init__(
            self,
            docker_list_thread,
            container_id,
            container_name,
            container_ports,
            container_labels,
            docker_client: docker.APIClient = Provide[Container.docker_client],
            draw_lock: RLock = Provide[Container.draw_lock],
    ):
        self.client = docker_client
        self.lock = draw_lock
        self.container_id = container_id
        self.docker_list_thread = docker_list_thread
        super().__init__(name='%s-%s' % (self.__class__.__name__, container_name))
        self.metrics = DockerContainerMetric(
            container_id=self.container_id,
            container_name=container_name,
            container_ports=container_ports,
            container_labels=container_labels,
            status='',
        )

    def get_container_metrics(self):
        return self.metrics

    def run(self):
        while not self.is_stopped():
            for stat in self.client.stats(self.container_id, True, True):
                if self.is_stopped():
                    return

                if stat['preread'][0:4] == '0001':
                    continue
                time_read = unix_time_millis(parse_date_time(stat['preread']))

                intervals = None
                if self.metrics is not None:
                    intervals = (time_read - self.metrics.time_read)
                with self.lock:
                    self.metrics = DockerContainerMetric(
                        container_id=self.metrics.container_id,
                        container_name=self.metrics.container_name,
                        container_ports=self.metrics.container_ports,
                        container_labels=self.metrics.container_labels,
                        status=self.metrics.status,
                        time_read=time_read,
                        cpu_percentage=self.calculate_cpu_percentage(stat, intervals),
                        cpu_percentage_previous=self.metrics.cpu_percentage if self.metrics is not None else None,
                        memory_usage=self.calculate_memory_usage(stat),
                        memory_usage_previous=self.metrics.memory_usage if self.metrics is not None else None,
                    )

    @staticmethod
    def calculate_memory_usage(stat):
        if 'usage' not in stat['memory_stats']:
            return None
        return stat['memory_stats']['usage']

    @staticmethod
    def calculate_cpu_percentage(stat, intervals):
        if intervals is None:
            return None
        if intervals == 0:
            return None
        if 'online_cpus' not in stat['cpu_stats']:
            return None

        usage = stat['cpu_stats']['cpu_usage']['total_usage'] - stat['precpu_stats']['cpu_usage']['total_usage']
        return usage / (intervals * stat['cpu_stats']['online_cpus'] * 100)
