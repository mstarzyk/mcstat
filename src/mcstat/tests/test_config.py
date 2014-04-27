from mcstat.config import Config, merge_configs


def test_merge_override():
    conf_default = Config(host='a')
    conf_override = Config(host='b')
    merged = merge_configs(conf_override, conf_default)
    assert merged.host == 'b'


def test_merge_empty():
    merged = merge_configs()
    assert merged.host is None


def test_merge():
    configs = [Config(host='a'), Config(user='b')]
    merged = merge_configs(*configs)
    assert merged.host == 'a'
    assert merged.user == 'b'
