class ContainerActions:
    LOG: str = 'log'
    SHELL: str = 'shell'
    KILL: str = 'kill'
    INSPECT: str = 'inspect'
    TAG: str = 'tag'


class SubprocessActions:
    LOG: str = 'log'
    START: str = 'start'
    STOP: str = 'stop'
    RESTART: str = 'restart'


class ComposeServiceActions:
    START: str = 'start'
    STOP: str = 'stop'
