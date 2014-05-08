from mcstat.core import ping, worker, receiver
from mcstat.net import is_multicast
from mcstat.config import make_config

import fcntl
import logging
import os
import signal
import sys
import threading


try:
    # Python 2
    from Queue import Queue
except ImportError:
    # Python 2
    from queue import Queue


log = logging.getLogger('mcstat.main')


class ThreadWithLog(threading.Thread):
    def run(self):
        try:
            log.info("Start")
            return threading.Thread.run(self)
        finally:
            log.info("End")


def make_nonblocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL, 0)
    flags = flags | os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)


# TODO
def signal_to_pipe(signal_number):
    """
    Returns read file descriptor of a pipe. This pipe will receive '\0' byte
    message when the main thread gets a signal.

    TODO: This should work only on the signal passed in the parameter, and
          ignore other signals.
    """

    pipe_read, pipe_write = os.pipe()
    make_nonblocking(pipe_write)

    signal.signal(signal.SIGINT, lambda signal, frame: None)
    signal.set_wakeup_fd(pipe_write)

    return pipe_read


def make_daemon(thread):
    thread.setDaemon(True)
    return thread


def main2(channels, interval, outputs, db_config):
    """
    :param channels: list of tuples (address, port)
    :param interval: interval in seconds for calculating statistics
    :param outputs: list of output keys
    :param db_config: database configuration
    """
    for ip, port in channels:
        assert is_multicast(ip)

    wake_up_fd = signal_to_pipe(signal.SIGINT)

    def make_queue():
        return Queue(1000)

    output_queues = []
    threads = []

    T = ThreadWithLog

    if 'db' in outputs:
        queue = make_queue()
        import mcstat.backend.db as DB
        output_queues.append(queue)
        thread = T(name="database", target=DB.worker, args=(queue, db_config))
        threads.append(thread)
    if 'stdout' in outputs:
        queue = make_queue()
        import mcstat.backend.console as C
        output_queues.append(queue)
        thread = make_daemon(T(name="stdout", target=C.worker, args=(queue,)))
        threads.append(thread)

    queue = make_queue()
    threads.extend([
        T(name="worker", target=worker, args=(interval, queue, output_queues)),
        T(name="receiver", target=receiver,
          args=(channels, queue, wake_up_fd)),
        make_daemon(T(name="ping", target=ping, args=(interval, queue)))
        ])

    for thread in threads:
        thread.start()


def setup_logging(level):
    logging.basicConfig(
        level=level,
        format='[%(levelname)-5s] (%(threadName)-8s) %(message)s'
        )


def main():
    config = make_config(sys.argv[1:])
    setup_logging(config.main.logging_level)
    log.debug("Configuration:\n%s", config)
    return main2(channels=config.main.channels,
                 interval=config.main.interval,
                 outputs=config.main.stats_output,
                 db_config=config.db
                 )
