import flowapp.utils
import datetime


def test_round_to_ten():
    """
    Test if the time is rounded correctly
    """
    d1 = datetime.datetime(2013, 9, 2, 16, 25, 59)
    d2 = datetime.datetime(2013, 9, 2, 16, 32, 59)
    dround = datetime.datetime(2013, 9, 2, 16, 30, 00)

    assert flowapp.utils.round_to_ten_minutes(d1) == dround
    assert flowapp.utils.round_to_ten_minutes(d2) == dround
