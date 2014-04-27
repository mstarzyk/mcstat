from mcstat.config import Config, DB, Main, merge_configs


def test_merge_override():
    conf_default = Config(db=DB(host='a'))
    conf_override = Config(db=DB(host='b'))
    merged = merge_configs(conf_override, conf_default)
    assert merged.db.host == 'b'


def test_merge_empty():
    merged = merge_configs()
    assert merged.db.host is None


def test_merge():
    merged = merge_configs(
        Config(db=DB(host='a')),
        Config(db=DB(user='b')),
        Config(main=Main(interval=2))
        )
    assert merged.db.host == 'a'
    assert merged.db.user == 'b'
    assert merged.main.interval == 2
