from tfscrap.__main__ import SPIDERS


def test_cli_registers_all_six_spiders():
    assert set(SPIDERS.keys()) == {
        "competitions",
        "clubs",
        "players",
        "appearances",
        "injuries",
        "transfers",
    }


def test_each_spider_has_a_name_attribute():
    for key, cls in SPIDERS.items():
        assert cls.name == key
