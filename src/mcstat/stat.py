from mcstat.domain import Metric


def metrics(timestamp, interval, channel, aggr):
    """
    :param timestamp: Timestamp of the metric.
    :type timestamp: Unix time (time.time)
    :param channel: The channel.
    :type channel: (string ip, port)
    :param interval: Lenght of time over which samples were collected
                     (in seconds).
    :param aggr: Aggretated samples.
    :type aggr: Aggr
    """
    return Metric(timestamp=timestamp,
                  channel=channel,
                  bitrate=float(aggr.bytes * 8) / 1024 / interval,
                  packets=float(aggr.packets) / interval
                  )
