from mcstat.net import is_multicast

import ConfigParser
import argparse
import logging


# TODO: Namespaces
_DB = ('query_sql', 'update_sql', 'host', 'database', 'user', 'password')
_MAIN = ('logging_level', 'addr', 'interval')


class Config(object):
    __slots__ = _MAIN + _DB


def load_config(file_name):
    """Loads configuration from the given file.

    Args:
      file_name: Path to the  configuration file.

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


def merge(args, config):
    """Merges configuration from commandline, and configuration file.

    Args:
      args: Commandline arguments (required)
      config: ConfigParser (optional)

    Returns:
      Config
    """
    ret = Config()
    if args.verbose:
        ret.logging_level = logging.DEBUG
    else:
        ret.logging_level = logging.INFO

    if config is None:
        pass

    ret.addr = list(set(args.addr))
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
    if args.config:
        config = load_config(args.config)
    else:
        config = None

    return merge(args, config)
