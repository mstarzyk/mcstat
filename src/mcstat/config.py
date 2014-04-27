from mcstat.net import is_multicast

import ConfigParser
import argparse
import logging
from collections import namedtuple


_Config = namedtuple('Config', ('main', 'db', 'statsd'))
_Main = namedtuple('Main', ('logging_level', 'channels', 'interval'))
_DB = namedtuple('DB', ('query_sql', 'update_sql', 'host', 'database',
                        'user', 'password')
                 )
_Statsd = namedtuple('Statsd', ('host', 'port'))


def with_defaults(cls, f=lambda key: None):
    def _(**kwargs):
        dd = dict(kwargs)
        for attr in cls._fields:
            if attr not in dd:
                dd[attr] = f(attr)
        return cls(**dd)
    return _


Main = with_defaults(_Main)
DB = with_defaults(_DB)
Statsd = with_defaults(_Statsd)
Config = with_defaults(_Config, lambda key: {'main': Main,
                                             'db': DB,
                                             'statsd': Statsd
                                             }[key]())


def load_config(file_name):
    """Loads configuration from file.

    Args:
      file_name: Configuration file path.

    Returns:
      Config
    """
    parser = ConfigParser.SafeConfigParser()
    parser.read(file_name)

    def cc(name, attrs):
        return {attr: parser.get(name, attr) for attr in attrs}

    db_config = cc('db', _DB._fields)
    statsd_config = cc('statsd', _Statsd._fields)

    return Config(db=DB(**db_config),
                  statsd=Statsd(**statsd_config)
                  )


def parse_commandline(args):
    """Parses commandline arguments.

    Args:
      args: Commandline arguments.

    Returns:
      arparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Multicast statistics.",
        epilog=None
        )
    parser.add_argument("-c", action='store', dest='config',
                        metavar="FILE",
                        help='Configuration file.'
                        )

    parser.add_argument("-v", action="store_true", dest="verbose",
                        help="Verbose output.", default=False)

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-s", action='store_const', dest='action',
                       const='output',
                       help='Print statistics to standard out.'
                       )
    group.add_argument("-d", action='store_const', dest='action',
                       const='db',
                       help='Write statistics to database.'
                       )

    default_interval = 1
    parser.add_argument("-n", dest='interval', type=int,
                        default=default_interval,
                        help="Interval in seconds (default={})".format(
                            default_interval)
                        )

    parser.add_argument("addr", metavar='addr', nargs='+',
                        type=multicast_address,
                        help='Multicast address (ip:port)'
                        )
    return parser.parse_args(args)


def multicast_address(string):
    """Argparse type of multicast address with port.

    Args:
      string: Text to be parsed as multicast address. Format: IP:PORT

    Returns:
      (string ip, port)
    """
    chunks = string.split(':', 1)
    if len(chunks) == 1:
        raise argparse.ArgumentTypeError(
            "Missing port: {!r}".format(string))

    addr, str_port = chunks

    try:
        port = int(str_port)
    except ValueError:
        raise argparse.ArgumentTypeError(
            "Invalid port: {!r}".format(str_port))

    if not is_multicast(addr):
        raise argparse.ArgumentTypeError(
            "Invalid multicast address: {!r}".format(addr))

    return (addr, port)


def merge_configs(*configs):
    """Merges configurations.

    Sets default values to None for all unset attributes.

    Args:
      config: Config objects, in the order of precendence.

    Returns:
      Merged config.
    """

    def full_vars(obj):
        return {key: value for key, value in vars(obj).items()
                if value is not None}

    def merge(a, b):
        dd = full_vars(b)
        dd.update(full_vars(a))
        ctor = with_defaults(type(a))
        return ctor(**dd)

    def merge_conf(a, b):
        return Config(main=merge(a.main, b.main),
                      db=merge(a.db, b.db),
                      statsd=merge(a.statsd, b.statsd)
                      )

    if len(configs) == 0:
        return Config()
    elif len(configs) == 1:
        return configs[0]
    else:
        left = configs[:2]
        right = configs[2:]
        return merge_configs(merge_conf(*left), *right)


def args_to_config(args):
    """Converts commandline arguments to Config.

    Args:
      args: Commandline arguments

    Returns:
      Config
    """
    logging_level = logging.DEBUG if args.verbose else logging.INFO

    return Config(main=Main(
        logging_level=logging_level,
        channels=tuple(set(args.addr)),
        interval=args.interval
        ))


def make_config(args):
    """Creates final configuration from commandline arguments.

    Loads optional configuration from file.

    Args:
      args: Parsed commandline arguments.

    Returns:
      Config
    """
    config = args_to_config(args)

    if args.config:
        return merge_configs(config, load_config(args.config))
    else:
        return config
