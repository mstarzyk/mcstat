from mcstat.net import make_multicast_server_socket

import select
import collections
import time
import logging

log = logging.getLogger('mcstat.core')


class Event(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def is_term(self):
        return False

    def is_tick(self):
        return False


class Term(Event):
    def is_term(self):
        return True


class Tick(Event):
    def is_tick(self):
        return True


class Stat(Event):
    def __init__(self, timestamp, channel, aggr):
        Event.__init__(self, timestamp)
        self.channel = channel
        self.aggr = aggr


class Aggr:
    def __init__(self, packets, bytes):
        self.packets = packets
        self.bytes = bytes

    def __iadd__(self, b):
        self.packets += b.packets
        self.bytes += b.bytes

    @classmethod
    def empty(cls):
        return Aggr(0, 0)


def receiver(channels, queue, wake_up_fd):
    # Maps file descriptor to (socket, (ip, port))
    socks_map = {}
    epoll = select.epoll()

    buffer = bytearray(4096)

    try:
        for ip, port in channels:
            sock = make_multicast_server_socket(ip, port)
            socks_map[sock.fileno()] = (sock, (ip, port))
            epoll.register(sock.fileno(), select.EPOLLIN)

        epoll.register(wake_up_fd, select.EPOLLIN)

        now = time.time()
        for _, channel in socks_map.values():
            queue.put_nowait(Stat(now, channel, Aggr.empty()))

        loop = True

        while loop:
            events = epoll.poll()
            now = time.time()
            for fileno, event in events:
                if fileno == wake_up_fd:
                    loop = False
                    break
                sock, channel = socks_map[fileno]
                num_bytes = sock.recv_into(buffer)
                queue.put_nowait(Stat(now, channel, Aggr(1, num_bytes)))
    finally:
        for sock, _ in socks_map.values():
            epoll.unregister(sock.fileno())
            sock.close()
        epoll.close()
        now = time.time()
        queue.put_nowait(Term(now))


def worker(queue):
    stats = collections.defaultdict(Aggr.empty)

    while True:
        try:
            event = queue.get()
            if event.is_term():
                break
            else:
                now = event.timestamp
                if event.is_tick():
                    log.debug("%.03f: Tick", now)
                    for (addr, port), aggr in stats.items():
                        print("{:f}\t{}\t{:d}\t{:d}\t{:d}".format(
                            now, addr, port, aggr.packets, aggr.bytes)
                            )
                    stats = {key: Aggr.empty() for key in stats}
                else:
                    aggr = stats[event.channel]
                    aggr += event.aggr
            queue.task_done()
        except:
            break


def ping(queue, interval):
    while True:
        time.sleep(interval)
        now = time.time()
        queue.put_nowait(Tick(now))
