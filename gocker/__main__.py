import logging
import pprint

import colored_traceback

from gocker.arguments import parse_main_args
from gocker.gui import gui

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

    init_logger(args.loglevel, GUI_LOG_FILE)
    logging.info("Starting gui")
    gui(args.docker_host, args.fsevents_address, args.fsevents_port)


if __name__ == "__main__":
    main()
