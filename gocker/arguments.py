import argparse
import logging
import os
import json
import shutil

from gocker.process import process_exec


class ArgumentAction:
    ACTION_GUI = 'gui'
    ACTION_SHORTCUT_LIST = 'shortcut-list'


def get_docker_socket_paths():
    for context_string in process_exec([shutil.which('docker'), "context", "ls", "--format", "json"]).split("\n"):
        context = json.loads(context_string)
        if context['Current']:
            yield context['DockerEndpoint'].replace('unix://', '')

    yield '/Users/%s/.colima/docker.sock' % os.getenv('USER')
    yield '/Users/%s/.docker/run/docker.sock' % os.getenv('USER')
    yield '/var/run/docker.sock'


def get_default_docker_socket():
    for path in get_docker_socket_paths():
        if not os.path.exists(path):
            continue
        return 'unix:/' + path
    return None


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
