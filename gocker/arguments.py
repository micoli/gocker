import argparse
import logging
import os


def parse_main_args():
    parser = argparse.ArgumentParser(
        description='gocker',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--debug',
        help='Print lots of debugging statements',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '--verbose',
        help='Be verbose',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    parser.add_argument(
        '--docker-host',
        help='docker-host',
        action='store',
        dest='docker_host',
        default='unix://Users/%s/.colima/docker.sock' % os.getenv('USER'),
    )
    parser.add_argument(
        '--fsevents-address',
        help='fsevents log address',
        dest='fsevents_address',
        default='127.0.0.1',
    )
    parser.add_argument(
        '--fsevents-port',
        help='fsevents log port',
        type=int,
        dest='fsevents_port',
        default=8087,
    )
    return parser
