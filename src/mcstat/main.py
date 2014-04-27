from mcstat.core import ping, worker, receiver
from mcstat.net import is_multicast
from mcstat.config import parse_commandline, make_config

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


def make_ping_thread(queue, interval):
    ping_thread = ThreadWithLog(name="ping", target=ping,
                                args=(queue, interval)
                                )
    # Ping thread is stateless, so we don't need to shut it down gracefully.
    ping_thread.setDaemon(True)
    return ping_thread


def main2(addr, interval):
    """
    addr - list of tuples (address, port)
    interval - interval in seconds for calculating statistics
    """
    for ip, port in addr:
        assert is_multicast(ip)

    wake_up_fd = signal_to_pipe(signal.SIGINT)
    queue = Queue(1000)

    threads = [
        ThreadWithLog(name="worker", target=worker, args=(queue, )),
        ThreadWithLog(name="receiver", target=receiver,
                      args=(addr, queue, wake_up_fd)),
        make_ping_thread(queue, interval)
        ]
    for thread in threads:
        thread.start()


def setup_logging(level):
    logging.basicConfig(
        level=level,
        format='[%(levelname)-5s] (%(threadName)-8s) %(message)s'
        )


def main():
    args = parse_commandline(sys.argv[1:])
    config = make_config(args)
    setup_logging(config.logging_level)
    log.debug("Configuration:\n%s", config)

    # actions = {'output': None,
    #            'db': None
    #            }

    return main2(addr=config.addr, interval=config.interval)
