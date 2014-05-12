mcstat
======
Mcstat listens to multicast traffic and outputs simple statistics.
For each channel it measures:

- throughput (KB/s),
- UDP packets (per second).

The output is written periodically to stdout or database (or both).

## Limitations
Mcstat currently reads channels from database once, so if the channel configuration changes, then 
mcstat should be restarted.

## Setup
### Requirements
- Python 2 and [Setuptools](https://pypi.python.org/pypi/setuptools) are required for installation.
- [VLC](https://en.wikipedia.org/wiki/VLC_media_player) is optional -- for smoke testing the installation.
- PostgreSQL database and [psycopg2](https://pypi.python.org/pypi/psycopg2) are required for writing statistics to database
 (PostgreSQL is the only database supported.)

### Installation as a non-root user
To install in $HOME/.local/ run:

```
cd src
python2 ./setup.py install --user
```

Then add mcstat to PATH, for example like this:

```
PATH=$PATH:$HOME/.local/bin
```

Mcstat can also be installed globally, or in a [virtual environment](https://pypi.python.org/pypi/virtualenv) -- 
just like any other Python package.

### Smoke test
To smoke test the installation get a sample [TS](https://en.wikipedia.org/wiki/MPEG_transport_stream) file
and stream it with VLC:

```
cvlc MY_STREAM.ts --loop --sout '#standard{access=udp,dst=239.0.0.2:1234}'
```

Then in another console run mcstat:

```
mcstat 239.0.0.2:1234
```

This will print statistics of a single channel to stdout.

Then stop mcstat with Ctrl-C.


### Configuration
Copy and customize the configuration file:

```
cp mcstat.conf SOME_PATH/
vim SOME_PATH/mcstat.conf
```

All configuration parameters are explained in the config file.


## Usage

To run mcstat:

```
mcstat -c SOME_PATH/usr/local/etc/mcstat.conf
```

To see help on commandline parameters:

```
mcstat --help
```
