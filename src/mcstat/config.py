from mcstat.net import is_multicast

import ConfigParser
import argparse
import logging
from collections import namedtuple


_DB = ('query_sql', 'update_sql', 'host', 'database', 'user', 'password')
_MAIN = ('logging_level', 'addr', 'interval')

_Config = namedtuple('Config', _MAIN + _DB)


def Config(**kwargs):
    dd = {attr: None for attr in (_MAIN + _DB)}
    dd.update(kwargs)
    return _Config(**dd)


def load_config(file_name):
    """Loads configuration from file.

    Args:
      file_name: Configuration file path.

    Returns:
      Config
    """
    parser = ConfigParser.SafeConfigParser()
    parser.read(file_name)

    db_config = {attr: parser.get('db', attr) for attr in _DB}
    return Config(**db_config)


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

    acc = {}
    for config in reversed(configs):
        non_empty_config = {key: value for key, value in vars(config).items()
                            if value is not None
                            }
        acc.update(non_empty_config)

    return Config(**acc)


def args_to_config(args):
    """Converts commandline arguments to Config.

    Args:
      args: Commandline arguments

    Returns:
      Config
    """
    logging_level = logging.DEBUG if args.verbose else logging.INFO

    return Config(logging_level=logging_level,
                  addr=tuple(set(args.addr)),
                  interval=args.interval
                  )


def make_config(args):
    """Creates final configuration from commandline arguments.

    Loads optional configuration from file.

    Args:
      args: Parsed commandline arguments.

    Returns:
      Config
    """
    configs = [args_to_config(args)]

    if args.config:
        configs.append(load_config(args.config))

    return merge_configs(*configs)
