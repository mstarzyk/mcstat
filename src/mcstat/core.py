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


def receiver(addr, queue, wake_up_fd):
    # Maps fileno to (socket, ip, port)
    socks_map = {}
    epoll = select.epoll()
    for ip, port in addr:
        sock = make_multicast_server_socket(ip, port)
        socks_map[sock.fileno()] = (sock, ip, port)
        epoll.register(sock.fileno(), select.EPOLLIN)

    epoll.register(wake_up_fd, select.EPOLLIN)

    loop = True

    buffer = bytearray(4096)

    try:
        now = time.time()
        for _, ip, port in socks_map.values():
            dst = (ip, port)
            queue.put_nowait(Stat(now, (dst, 0, 0)))
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
                queue.put_nowait(Stat(now, (dst, 1, data_len)))
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
                    for (addr, port), aggr in stats.items():
                        print("{:f}\t{}\t{:d}\t{:d}\t{:d}".format(
                            now, addr, port, aggr.packets, aggr.bytes)
                            )
                        aggr.packets = 0
                        aggr.bytes = 0
                else:
                    dst, packets, len_data = event.data
                    aggr = stats[dst]
                    aggr.packets += packets
                    aggr.bytes += len_data
            queue.task_done()
        except:
            break


def ping(queue, interval):
    while True:
        time.sleep(interval)
        now = time.time()
        queue.put_nowait(Tick(now))
