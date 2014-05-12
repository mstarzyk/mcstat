import psycopg2
import datetime
from contextlib import closing


class DB(object):
    def __init__(self, config):
        self.config = config
        self._connection = None

    def close(self):
        if self._connection is not None:
            self._connection.close()
        self._connection = None

    @property
    def connection(self):
        if self._connection is None:
            config = self.config
            self._connection = psycopg2.connect(
                database=config.database,
                user=config.user,
                host=config.host,
                password=config.password
                )
        return self._connection

    def get_channels(self):
        return self.retry(self._get_channels)

    def write(self, channel_metrics):
        return self.retry(self._write, channel_metrics)

    def _get_channels(self):
        with self.connection.cursor() as cursor:
            cursor.execute(self.config.query_sql)
            rows = cursor.fetchall()
            return [(ip, int(port)) for ip, port in rows]

    def _write(self, channel_stats):
        with self.connection.cursor() as cursor:
            params = [cs for cs in channel_stats]
            cursor.executemany(self.config.update_sql, params)
            self.connection.commit()

    def retry(self, fun, *args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except (psycopg2.InterfaceError, psycopg2.OperationalError):
            self.close()
            return fun(*args, **kwargs)


# TODO: Send events in batches
def worker(queue, db_config):
    def ts(timestamp):
        return datetime.datetime.fromtimestamp(timestamp)

    with closing(DB(db_config)) as db:
        while True:
            event = queue.get()
            if event.is_term():
                break
            else:
                metric = event.metric
                ip, port = metric.channel
                row = {'timestamp': ts(metric.timestamp),
                       'ip': ip,
                       'port': port,
                       'bitrate': metric.bitrate,
                       'packets': metric.packets
                       }
                db.write([row])


def get_channels(db_config):
    with closing(DB(db_config)) as db:
        return db.get_channels()
