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
    # Python 3
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


def signal_to_pipe(*signal_numbers):
    """
    Returns read file descriptor of a pipe. This pipe will receive '\0' byte
    message when the main thread gets a signal.

    :param signal_numbers: list of signals whose default handler should be
    disabled, so that application can shut down gracefully.

    :return: Read file descriptor that will receive '\0' on signal.
    """

    pipe_read, pipe_write = os.pipe()
    make_nonblocking(pipe_write)

    do_nothing = lambda signal, frame: None
    for num in signal_numbers:
        signal.signal(num, do_nothing)
    signal.set_wakeup_fd(pipe_write)

    return pipe_read


def make_daemon(thread):
    thread.setDaemon(True)
    return thread


def main2(main_config, db_config):
    """
    :type main_config: mcstat.config._Main
    :type db_config: mcstat.config._DB
    """

    channels = main_config.channels
    interval = main_config.interval
    outputs = main_config.stats_output

    for ip, port in channels:
        assert is_multicast(ip)

    wake_up_fd = signal_to_pipe(signal.SIGINT, signal.SIGTERM)

    def make_queue():
        return Queue(1000)

    output_queues = []
    threads = []

    T = ThreadWithLog

    if main_config.channels_from_db:
        import mcstat.backend.db as DB
        channels = DB.get_channels(db_config)
        log.info("Loaded %d channels from database.", len(channels))
    channels = sorted(channels)
    for i, channel in enumerate(channels, 1):
        log.info("Channel %s: %s:%d", i, channel[0], channel[1])

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
    return main2(main_config=config.main,
                 db_config=config.db
                 )
