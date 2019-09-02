import flowapp.utils
from datetime import datetime, timedelta
import ipaddress
import pytest


def test_get_rule_state_by_time():
    """
    Test if time in the past returns 2
    """
    past = datetime.now() - timedelta(days=1)

    assert flowapp.utils.get_state_by_time(past) == 2


def test_round_to_ten():
    """
    Test if the time is rounded correctly
    """
    d1 = datetime(2013, 9, 2, 16, 25, 59)
    d2 = datetime(2013, 9, 2, 16, 32, 59)
    dround = datetime(2013, 9, 2, 16, 30, 00)

    assert flowapp.utils.round_to_ten_minutes(d1) == dround
    assert flowapp.utils.round_to_ten_minutes(d2) == dround


@pytest.mark.parametrize("address_a, address_b", [
    (u"2001:718:1c01:16:f1c4:c682:817:7e23", u"2001:0718:1c01:0016:f1c4:c682:0817:7e23"),
    (u"2001:718::", u"2001:718::0"),
    (u"2001:718::0", u"2001:0718:0000:0000:0000:0000:0000:0000")

])
def test_ipv6_comparsion(address_a, address_b):
    assert ipaddress.ip_address(address_a) == ipaddress.ip_address(address_b)
