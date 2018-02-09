import pytest
import flowspec


def test_translate_number():
    """
    tests for x (integer)  to =x
    """
    assert "=10" == flowspec.translate_sequence("10")


def test_raises():
    """
    tests for translator
    """
    with pytest.raises(ValueError):
        flowspec.translate_sequence("ahoj")


def test_raises_bad_number():
    """
    tests for translator
    """
    with pytest.raises(ValueError):
        flowspec.translate_sequence("75555")


def test_translate_range():
    """
    tests for x-y  to >=x&<=y
    """
    assert ">=10&<=20" == flowspec.translate_sequence("10-20")


def test_exact_rule():
    """
    test for >=x&<=y to >=x&<=y
    """
    assert ">=10&<=20" == flowspec.translate_sequence(">=10&<=20")


def test_greater_than():
    """
    test for >x to >=x&<=65535
    """
    assert ">=10&<=65535" == flowspec.translate_sequence(">10")


def test_greater_equal_than():
    """
    test for >=x to >=x&<=65535
    """
    assert ">=10&<=65535" == flowspec.translate_sequence(">=10")


def test_lower_than():
    """
    test for <x to >=0&<=0
    """
    assert ">=0&<=10" == flowspec.translate_sequence("<10")


def test_lower_equal_than():
    """
    test for <x to >=0&<=0
    """
    assert ">=0&<=10" == flowspec.translate_sequence("<=10")
