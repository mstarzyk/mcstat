class Event(object):
    """Base event sent via channels between threads."""
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def is_term(self):
        return False

    def is_tick(self):
        return False


class Term(Event):
    """Program termination."""
    def is_term(self):
        return True


class Tick(Event):
    """Sent every second."""
    def is_tick(self):
        return True


class Sample(Event):
    """Data sample."""
    def __init__(self, timestamp, channel, aggr):
        Event.__init__(self, timestamp)
        self.channel = channel
        self.aggr = aggr


class MetricEvent(Event):
    """Event with metric."""
    def __init__(self, metric):
        """
        :type metric: Metric
        """
        Event.__init__(self, metric.timestamp)
        self.metric = metric


class Aggr(object):
    """Accumulates values of data samples."""
    def __init__(self, packets, bytes):
        self.packets = packets
        self.bytes = bytes

    def __iadd__(self, b):
        self.packets += b.packets
        self.bytes += b.bytes

    @classmethod
    def empty(cls):
        return Aggr(0, 0)


class Metric(object):
    """Metrics for channel: bitrate and packets/second."""
    def __init__(self, timestamp, channel, bitrate, packets):
        """
        :param timestamp: Date/time of the metric.
        :type timestamp: datetime.datetime
        :param channel: The channel.
        :type channel: (string ip, port)
        :param bitrate: kbits/second
        :param packets: packets/second
        """
        self.timestamp = timestamp
        self.channel = channel
        self.bitrate = bitrate
        self.packets = packets
