import psycopg2 as dbapi


class DB(object):
    def __init__(self, config):
        self.conn = dbapi.connect(database=config.database,
                                  user=config.user,
                                  host=config.host,
                                  password=config.password
                                  )
        self.config = config

    def get_channels(self):
        with self.conn.cursor() as cursor:
            cursor.execute(self.config.query_sql)
            rows = cursor.fetchall()
            return [(ip, int(port)) for ip, port in rows]

    def write(self, channel_stats):
        with self.conn.cursor() as cursor:
            cursor.executemany(self.config.update_sql)
            # for channel, stat in channel_stats:
            self.conn.commit()
