from queue import Queue
from threading import RLock

import docker
from dependency_injector import containers, providers
from event_bus import EventBus


# pylint: disable=c-extension-no-member
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    draw_lock = providers.ThreadSafeSingleton(
        RLock
    )

    docker_client = providers.ThreadSafeSingleton(
        docker.APIClient,
        base_url=config.docker.host_url
    )
    queue = providers.Singleton(
        Queue
    )

    bus = providers.Singleton(
        EventBus
    )
