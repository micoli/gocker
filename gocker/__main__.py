import logging
import pprint
import sys

import colored_traceback
from tabulate import tabulate

from gocker.arguments import parse_main_args, ArgumentAction
from gocker.gui import gui
from gocker.gui.shortcut import shortcuts

colored_traceback.add_hook(always=True)
pp = pprint.PrettyPrinter(indent=4)

GUI_LOG_FILE = '/tmp/gocker-gui.log'


def init_logger(level, filename=None):
    _format = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
    _date_format = '%Y-%m-%d %H:%M:%S'
    logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)
    if filename is not None:
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            level=level,
            filename=filename,
            format=_format,
            datefmt=_date_format
        )
        return logging.root.handlers[0]
    logging.basicConfig(
        level=level,
        format=_format,
        datefmt=_date_format
    )
    return None


def main() -> None:
    parser = parse_main_args()
    args = parser.parse_args()

    if args.action == ArgumentAction.ACTION_GUI:
        init_logger(args.loglevel, GUI_LOG_FILE)
        logging.info("Starting gui")
        gui(args.docker_host, args.fsevents_address, args.fsevents_port)
        sys.exit(0)

    if args.action == ArgumentAction.ACTION_SHORTCUT_LIST:
        table = []
        for shortcut in shortcuts.values():
            table.append([
                shortcut.key,
                shortcut.message,
            ])
        print(tabulate(table, headers=[
            "Key",
            "Message",
        ], tablefmt="fancy_grid"))
        sys.exit(0)

    parser.print_help(sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
