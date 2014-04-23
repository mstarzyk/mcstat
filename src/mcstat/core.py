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
    def __init__(self, timestamp, data):
        Event.__init__(self, timestamp)
        self.data = data


class Aggr:
    packets = 0
    bytes = 0


def receiver(addrs, queue, wake_up_fd):
    # Maps fileno to (socket, ip, port)
    socks_map = {}
    epoll = select.epoll()
    for ip, port in addrs:
        sock = make_multicast_server_socket(ip, port)
        socks_map[sock.fileno()] = (sock, ip, port)
        epoll.register(sock.fileno(), select.EPOLLIN)

    epoll.register(wake_up_fd, select.EPOLLIN)

    loop = True

    buffer = bytearray(4096)

    try:
        while loop:
            events = epoll.poll()
            now = time.time()
            for fileno, event in events:
                if fileno == wake_up_fd:
                    loop = False
                    queue.put(Term(now))
                    break
                sock, ip, port = socks_map[fileno]
                data_len = sock.recv_into(buffer)
                dst = (ip, port)
                queue.put_nowait(Stat(now, (dst, data_len)))
    finally:
        for sock, ip, port in socks_map.values():
            epoll.unregister(sock.fileno())
            sock.close()
        epoll.close()


def worker(queue):
    stats = collections.defaultdict(Aggr)

    while True:
        try:
            event = queue.get()
            if event.is_term():
                break
            else:
                now = event.timestamp
                if event.is_tick():
                    log.debug("%.03f: Tick", now)
                    for key, aggr in stats.items():
                        log.debug("  %s:\t%d\t%d", key, aggr.packets,
                                  aggr.bytes)
                        aggr.packets = 0
                        aggr.bytes = 0
                else:
                    dst, len_data = event.data
                    aggr = stats[dst]
                    aggr.packets += 1
                    aggr.bytes += len_data
            queue.task_done()
        except:
            break


def ping(queue):
    while True:
        time.sleep(1)
        now = time.time()
        queue.put_nowait(Tick(now))
