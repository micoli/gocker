import inspect
# import logging
from functools import wraps

from event_bus import EventBus


def listener(func):
    @wraps(func)
    def inner(self, *args, **kwargs):
        # logging.debug(['event', func, args, kwargs])
        return func(self, *args, **kwargs)

    return inner


def set_listeners(instance, bus: EventBus):
    source_lines = inspect.getsourcelines(instance.__class__)[0]
    for i, line in enumerate(source_lines):
        if line.strip() == '@listener':
            function_name = source_lines[i + 1].split('def')[1].split('(')[0].strip()
            listener_function = getattr(instance, function_name)
            parameters = list(inspect.signature(listener_function).parameters.items())

            if not len(parameters) == 1:
                raise Exception('Number of arguments to a listener must be one and be typehinted to eventClassName')

            if parameters[0][1].annotation is None:
                raise Exception('First argument to a listener must be typehinted to eventClassName')

            bus.add_event(listener_function, parameters[0][1].annotation.__name__)
