from mcstat.net import is_multicast

import ConfigParser
import argparse
import logging
from collections import namedtuple

default_interval = 1

_Config = namedtuple('Config', ('main', 'db'))
_Main = namedtuple('Main', ('logging_level', 'channels', 'interval',
                            'stats_output', 'channels_from_db')
                   )
_DB = namedtuple('DB', ('query_sql', 'update_sql', 'host', 'database',
                        'user', 'password')
                 )


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
Config = with_defaults(_Config, lambda key: {'main': Main,
                                             'db': DB,
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

    def zz(name, section='main', get=parser.get, proc=lambda x: x):
        if parser.has_option(section, name):
            return proc(get(section, name))
        else:
            return None

    def cc(name, attrs):
        return {attr: parser.get(name, attr) for attr in attrs
                if parser.has_option(name, attr)
                }

    db_config = cc('db', _DB._fields)

    split = lambda x: x.split()
    addr = lambda x: tuple({multicast_address(a) for a in x.split()})
    main = Main(channels_from_db=zz('channels_from_db', get=parser.getboolean),
                interval=zz('interval', get=parser.getint),
                channels=zz('channels', proc=addr),
                stats_output=zz('stats_output', proc=split)
                )

    return Config(main=main,
                  db=DB(**db_config)
                  )


def commandline_parser():
    """Creates commandline arguments parser.

    Returns:
      arparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Multicast statistics.",
        epilog=None
        )
    parser.add_argument("-v", action="store_true", dest="verbose",
                        help="Verbose output.", default=False)

    parser.add_argument("-c", action='store', dest='config',
                        metavar="FILE",
                        help='Configuration file.'
                        )

    parser.add_argument("-n", action='append_const', dest='stats_output',
                        const='stdout',
                        help='Write statistics to standard out only.'
                        )

    parser.add_argument("-i", dest='interval', type=int,
                        help="Interval in seconds (default={}).".format(
                            default_interval)
                        )

    parser.add_argument("channel", metavar='channel', nargs='*',
                        type=multicast_address,
                        help='Multicast address (ip:port). If not specified' +
                             ' here, then channels should be set in' +
                             ' configuration file or read from database.'
                        )
    return parser


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

    channels = tuple(set(args.channel)) or None

    main = Main(
        logging_level=logging_level,
        channels=channels,
        channels_from_db=False if channels else None,
        interval=args.interval
        )
    return Config(main=main)


def make_config(args):
    """Creates final configuration from commandline arguments.

    Loads optional configuration from file.

    Args:
      args: Commandline arguments.

    Returns:
      Config
    """
    parser = commandline_parser()
    args = parser.parse_args(args)
    all_configs = [args_to_config(args)]
    if args.config:
        all_configs.append(load_config(args.config))
    defaults = Config(main=Main(
        interval=default_interval,
        stats_output=['stdout'],
        channels_from_db=False
        ))
    all_configs.append(defaults)
    config = merge_configs(*all_configs)
    if not (config.main.channels or config.main.channels_from_db):
        parser.error("No channels specified.")
    return config
