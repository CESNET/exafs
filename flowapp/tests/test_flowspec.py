import pytest
from flowapp.flowspec import translate_sequence, filter_rules_action, check_limit


def test_translate_number():
    """
    tests for x (integer)  to =x
    """
    assert "[=10]" == translate_sequence("10")


def test_raises():
    """
    tests for translator
    """
    with pytest.raises(ValueError):
        translate_sequence("ahoj")


def test_raises_bad_number():
    """
    tests for translator
    """
    with pytest.raises(ValueError):
        translate_sequence("75555")


def test_translate_range():
    """
    tests for x-y  to >=x&<=y
    """
    assert "[>=10&<=20]" == translate_sequence("10-20")


def test_exact_rule():
    """
    test for >=x&<=y to >=x&<=y
    """
    assert "[>=10&<=20]" == translate_sequence(">=10&<=20")


def test_greater_than():
    """
    test for >x to >=x&<=65535
    """
    assert "[>=10&<=65535]" == translate_sequence(">10")


def test_greater_equal_than():
    """
    test for >=x to >=x&<=65535
    """
    assert "[>=10&<=65535]" == translate_sequence(">=10")


def test_lower_than():
    """
    test for <x to >=0&<=0
    """
    assert "[>=0&<=10]" == translate_sequence("<10")


def test_lower_equal_than():
    """
    test for <x to >=0&<=0
    """
    assert "[>=0&<=10]" == translate_sequence("<=10")


# new tests


def test_multiple_sequences():
    """Test multiple sequences separated by semicolons"""
    assert "[=10 >=20&<=30]" == translate_sequence("10;20-30")
    assert "[=10 >=0&<=20 >=30&<=65535]" == translate_sequence("10;<=20;>30")


def test_empty_sequence():
    """Test empty sequence and sequences with empty parts"""
    assert "[]" == translate_sequence("")
    assert "[=10]" == translate_sequence("10;;")
    assert "[=10 =20]" == translate_sequence("10;;20")


def test_range_edge_cases():
    """Test edge cases for ranges"""
    # Same numbers in range
    assert "[>=10&<=10]" == translate_sequence("10-10")

    # Invalid range (start > end)
    with pytest.raises(ValueError, match="Invalid range: start value cannot be greater than end value"):
        translate_sequence("20-10")

    # Invalid range in exact rule
    with pytest.raises(ValueError, match="Invalid range: start value cannot be greater than end value"):
        translate_sequence(">=20&<=10")


def test_check_limit_validation():
    """Test the check_limit function"""
    # Test valid cases
    assert check_limit(10, 100) == 10
    assert check_limit(0, 100, 0) == 0
    assert check_limit(100, 100, 0) == 100

    # Test invalid cases
    with pytest.raises(ValueError, match="Invalid value number: .* is too big"):
        check_limit(101, 100)

    with pytest.raises(ValueError, match="Invalid value number: .* is too small"):
        check_limit(-1, 100, 0)


def test_invalid_inputs():
    """Test various invalid inputs"""
    invalid_inputs = [
        "abc",  # Non-numeric
        "10.5",  # Decimal
        "10,20",  # Wrong separator
        "10&20",  # Wrong format
        ">",  # Incomplete
        ">=",  # Incomplete
        "<",  # Incomplete
        "<=",  # Incomplete
        ">>10",  # Invalid operator
        "<<10",  # Invalid operator
        ">=10&",  # Incomplete range
        "&<=10",  # Incomplete range
    ]

    for invalid_input in invalid_inputs:
        with pytest.raises(ValueError):
            translate_sequence(invalid_input)


class MockRule:
    def __init__(self, action_id):
        self.action_id = action_id


def test_filter_rules_action():
    """Test the filter_rules_action function"""
    # Create test rules
    rules = [MockRule(1), MockRule(2), MockRule(3), MockRule(4)]

    # Test with empty allowed actions
    editable, viewonly = filter_rules_action([], rules)
    assert len(editable) == 0
    assert len(viewonly) == 4

    # Test with some allowed actions
    editable, viewonly = filter_rules_action([1, 3], rules)
    assert len(editable) == 2
    assert len(viewonly) == 2
    assert all(rule.action_id in [1, 3] for rule in editable)
    assert all(rule.action_id in [2, 4] for rule in viewonly)

    # Test with all actions allowed
    editable, viewonly = filter_rules_action([1, 2, 3, 4], rules)
    assert len(editable) == 4
    assert len(viewonly) == 0

    # Test with empty rules list
    editable, viewonly = filter_rules_action([1, 2], [])
    assert len(editable) == 0
    assert len(viewonly) == 0
