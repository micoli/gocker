import math
from dataclasses import dataclass


@dataclass
class Shortcut:
    key: str
    message: str
    builtin: bool
    short_message: str = None


shortcuts = {
    'QUIT': Shortcut('q', 'quit', True, 'quit'),
    'SHOW_SHORTCUTS': Shortcut('?', 'show help', True, 'help'),
    'KILL_CONTAINER': Shortcut('k', 'kill container', True),
    'TAG_CONTAINER': Shortcut(' ', 'tag container', True),
    'INSPECT_CONTAINER': Shortcut('i', 'inspect container', True),
    'CONTAINER_SHELL': Shortcut('s', 'shell in container', True),
    'SUBPROCESS_START_STOP': Shortcut('s', 'start/stop in subprocess', True),
    'SUBPROCESS_RESTART': Shortcut('r', 'restart in subprocess', True),
    'COMPOSER_SERVICES_START_STOP': Shortcut('s', 'start/stop composer service', True),
    'SELECT_PREVIOUS_SORT_COLUMN': Shortcut('<', 'previous sort column', True),
    'SELECT_NEXT_SORT_COLUMN': Shortcut('>', 'next sort column', True),
    'SELECT_TOGGLE_SORT_ORDER': Shortcut('o', 'toggle sort order', True),
    'SHOW_LOG': Shortcut('l', 'show logs', True),
    'SHOW_ALL_LOG': Shortcut('L', 'show all logs', True),
    'LOG_MARKER': Shortcut('M', 'Add a marker in logs', True),
    'SELECT_NEXT_PANE': Shortcut('tab', 'select next pane', True, 'next'),
    'SELECT_PREVIOUS_PANE': Shortcut('shift tab', 'select previous pane', True, 'previous'),
}


def get_shortcut_by_key(key: str, builtin: bool):
    for shortcut in shortcuts.values():
        if shortcut.key == key and shortcut.builtin == builtin:
            return shortcut
    return None


def shortcut_list():
    return ' '.join(list(map(
        lambda shortcut: '[%s] %s' % (
            shortcut.key, shortcut.short_message if shortcut.short_message is not None else shortcut.message
        ),
        shortcuts.values()
    )))


# pylint: disable=c-extension-no-member
def shortcut_list_chunks(number_of_chunks):
    shortcut_text_list = list(map(
        lambda shortcut: '[%s] %s' % (
            shortcut.key, shortcut.short_message if shortcut.short_message is not None else shortcut.message
        ),
        shortcuts.values()
    ))
    chunk_size = int(math.ceil(len(shortcut_text_list) / number_of_chunks))
    return [shortcut_text_list[i:i + chunk_size] for i in range(0, len(shortcut_text_list), chunk_size)]
