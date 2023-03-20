import ipaddress
import pytest

from datetime import datetime, timedelta

from flowapp import utils


@pytest.mark.parametrize(
    "apitime, preformat",
    [
        ("10/15/2015 14:46", "us"),
        ("2015/10/15 14:46", "yearfirst"),
        ("1444913400", "timestamp"),
        (1444913400, "timestamp"),
    ],
)
def test_parse_api_time(apitime, preformat):
    """
    is the time parsed correctly
    """
    result = utils.parse_api_time(apitime)
    assert isinstance(result, tuple)
    assert result[0] == datetime(2015, 10, 15, 14, 50)
    assert result[1] == preformat


@pytest.mark.parametrize(
    "apitime", ["10/152015 14:46", "201/10/15 14:46", "144123254913400", "abcd"]
)
def test_parse_api_time_bad_time(apitime):
    """
    is the time parsed correctly
    """
    assert not utils.parse_api_time(apitime)


def test_get_rule_state_by_time():
    """
    Test if time in the past returns 2
    """
    past = datetime.now() - timedelta(days=1)

    assert utils.get_state_by_time(past) == 2


def test_round_to_ten():
    """
    Test if the time is rounded correctly
    """
    d1 = datetime(2013, 9, 2, 16, 25, 59)
    d2 = datetime(2013, 9, 2, 16, 32, 59)
    dround = datetime(2013, 9, 2, 16, 30, 00)

    assert utils.round_to_ten_minutes(d1) == dround
    assert utils.round_to_ten_minutes(d2) == dround


@pytest.mark.parametrize(
    "address_a, address_b",
    [
        (
            "2001:718:1c01:16:f1c4:c682:817:7e23",
            "2001:0718:1c01:0016:f1c4:c682:0817:7e23",
        ),
        ("2001:718::", "2001:718::0"),
        ("2001:718::0", "2001:0718:0000:0000:0000:0000:0000:0000"),
    ],
)
def test_ipv6_comparsion(address_a, address_b):
    assert ipaddress.ip_address(address_a) == ipaddress.ip_address(address_b)
