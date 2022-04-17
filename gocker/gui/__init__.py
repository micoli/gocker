import logging
import sys
import threading

import gocker
from gocker.gui.app import App
from gocker.gui.dependency_injection import Container
from gocker.threads import StoppableThread


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def handle_threading_exception(args):
    if issubclass(args.exc_type, KeyboardInterrupt):
        sys.__excepthook__(args.exc_type, args.exc_value, args.exc_traceback)
        return

    logging.error("Uncaught exception in thread %s" % args.thread.name,
                  exc_info=(args.exc_type, args.exc_value, args.exc_traceback))


def update_gui(stop_event, message_queue):
    while not stop_event.wait(timeout=1.0):
        message_queue.put('')


def gui(docker_host_url, fsevent_address, fsevent_port):
    sys.excepthook = handle_exception
    threading.excepthook = handle_threading_exception
    container = Container()

    container.config.docker.host_url.from_value(docker_host_url)
    container.config.fsevents.address.from_value(fsevent_address)
    container.config.fsevents.port.from_value(fsevent_port)
    container.wire(packages=[gocker])

    gui_app = App()

    gui_updater_thread = StoppableThread(
        target=update_gui, args=[threading.Event(), container.queue()],
        name='gui_updater',
    )
    try:
        gui_updater_thread.start()
        gui_app.loop.screen.set_terminal_properties(colors=256)
        gui_app.loop.run()
    except KeyboardInterrupt:
        gui_updater_thread.stop()
        gui_app.stop()
