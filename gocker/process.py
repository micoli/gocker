import logging
import subprocess


def process_exec(args, cwd=None):
    logging.debug('Launching "%s" in "%s"' % (' '.join(args), cwd if cwd is not None else '-'))
    try:
        return subprocess.run(args, capture_output=True, check=True, cwd=cwd).stdout.decode("utf-8").strip("\n")
    except subprocess.CalledProcessError as error:
        error.cmd = '%s\n%s' % (error.cmd, str(' '.join(args)))
        raise error


def process_exec_detached(args, cwd):
    logging.debug('Launching detached "%s" in "%s"' % (' '.join(args), cwd))
    try:
        # pylint: disable=consider-using-with
        subprocess.Popen(
            args,
            cwd=cwd,
            start_new_session=True
        )
    except subprocess.CalledProcessError as error:
        error.cmd = '%s\n%s' % (error.cmd, str(' '.join(args)))
        raise error
