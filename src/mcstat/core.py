from mcstat.net import make_multicast_server_socket
from mcstat.domain import Term, Tick, Sample, Aggr, MetricEvent
from mcstat.stat import metrics

import select
import collections
import time
import logging

log = logging.getLogger('mcstat.core')


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
            queue.put_nowait(Sample(now, channel, Aggr.empty()))

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
                queue.put_nowait(Sample(now, channel, Aggr(1, num_bytes)))
    finally:
        for sock, _ in socks_map.values():
            epoll.unregister(sock.fileno())
            sock.close()
        epoll.close()
        send_term(queue)


def send_term(*queues):
    """Send termination event to the given queue."""
    now = time.time()
    for queue in queues:
        queue.put_nowait(Term(now))


def worker(interval, queue_in, queues_out):
    aggrs = collections.defaultdict(Aggr.empty)

    def send_all(obj):
        for queue in queues_out:
            queue.put_nowait(obj)

    try:
        while True:
            event = queue_in.get()
            if event.is_term():
                send_all(event)
                break
            else:
                if event.is_tick():
                    now = event.timestamp
                    log.debug("%.03f: Tick", now)
                    for channel, aggr in aggrs.items():
                        m = metrics(now, interval, channel, aggr)
                        send_all(MetricEvent(m))
                    aggrs = {key: Aggr.empty() for key in aggrs}
                else:
                    aggr = aggrs[event.channel]
                    aggr += event.aggr
            queue_in.task_done()
    finally:
        send_term(*queues_out)


def ping(interval, queue):
    while True:
        time.sleep(interval)
        now = time.time()
        queue.put_nowait(Tick(now))
