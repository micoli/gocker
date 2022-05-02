import argparse
import logging
import os


class ArgumentAction:
    ACTION_GUI = 'gui'
    ACTION_SHORTCUT_LIST = 'shortcut-list'


def get_default_docker_socket():
    docker_path = '/Users/%s/.colima/docker.sock' % os.getenv('USER')
    if os.path.exists(docker_path):
        return 'unix:/' + docker_path
    return 'unix://var/run/docker.sock'


def parse_main_args():
    parser = argparse.ArgumentParser(
        description='gocker',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--action',
        action='store',
        dest='action',
        choices=[getattr(ArgumentAction, name) for name in dir(ArgumentAction) if name.startswith('ACTION_')],
        default=ArgumentAction.ACTION_GUI,
    )
    parser.add_argument(
        '--verbose',
        help='Be verbose',
        action='store_const',
        dest='loglevel',
        const=logging.INFO,
    )
    parser.add_argument(
        '--debug',
        help='Be very verbose',
        action='store_const',
        dest='loglevel',
        const=logging.DEBUG,
        default=logging.WARNING,
    )
    parser.add_argument(
        '--docker-host',
        help='docker-host',
        action='store',
        dest='docker_host',
        default=get_default_docker_socket(),
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
