from mcstat.net import is_multicast

import ConfigParser
import argparse
import logging
import pprint


_DB = ('query_sql', 'update_sql', 'host', 'database', 'user', 'password')
_MAIN = ('logging_level', 'addr', 'interval')


class Config(object):
    # TODO: Split configuration params into Namespaces?
    # TODO: Do not use slots?
    __slots__ = _MAIN + _DB

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attrs = {}
        for attr in self.__slots__:
            if hasattr(self, attr):
                attrs[attr] = getattr(self, attr)
        return pprint.pformat(attrs)

    def fill_default_args(self):

        for attr in self.__slots__:
            if not hasattr(self, attr):
                setattr(self, attr, None)


def load_config(file_name):
    """Loads configuration from file.

    Args:
      file_name: Configuration file path.

    Returns:
      Config
    """
    parser = ConfigParser.SafeConfigParser()
    parser.read(file_name)

    config = Config()

    for option in ('query_sql', 'update_sql', 'host', 'database',
                   'user', 'password'):
        setattr(config, option, parser.get('db', option))
    return config


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

    ret = Config()

    for config in reversed(configs):
        for attr in Config.__slots__:
            if hasattr(config, attr):
                setattr(ret, attr, getattr(config, attr))

    ret.fill_default_args()

    return ret


def args_to_config(args):
    """Converts commandline arguments to Config.

    Args:
      args: Commandline arguments

    Returns:
      Config
    """
    ret = Config()
    if args.verbose:
        ret.logging_level = logging.DEBUG
    else:
        ret.logging_level = logging.INFO

    ret.addr = tuple(set(args.addr))
    ret.interval = args.interval

    return ret


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
