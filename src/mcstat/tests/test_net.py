# import py.test

from mcstat.net import is_multicast


def test_is_multicast():
    assert is_multicast("224.0.0.0")
    assert is_multicast("239.0.0.0")
    assert not is_multicast("240.0.0.0")
    assert not is_multicast("223.255.255.255")
