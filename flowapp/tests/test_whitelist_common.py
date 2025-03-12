import pytest
from flowapp.services.whitelist_common import (
    Relation,
    check_rule_against_whitelists,
    check_whitelist_against_rules,
    check_whitelist_to_rule_relation,
    subtract_network,
    clear_network_cache,
)


# Tests for core function that checks network relations
@pytest.mark.parametrize(
    "rule,whitelist,expected",
    [
        # IPv4 test cases
        ("192.168.1.0/24", "192.168.0.0/16", Relation.SUPERNET),  # Whitelist is supernet
        ("192.168.1.0/24", "192.168.1.0/24", Relation.EQUAL),  # Equal networks
        ("192.168.1.0/24", "192.168.1.128/25", Relation.SUBNET),  # Whitelist is subnet
        ("192.168.1.128/25", "192.168.1.0/24", Relation.SUPERNET),  # Whitelist is supernet
        ("10.0.0.0/8", "192.168.1.0/24", Relation.DIFFERENT),  # Different networks
        # IPv6 test cases
        ("2001:db8::/32", "2001:db8::/32", Relation.EQUAL),  # Equal networks
        ("2001:db8:1::/48", "2001:db8::/32", Relation.SUPERNET),  # Whitelist is supernet
        ("2001:db8::/32", "2001:db8:1::/48", Relation.SUBNET),  # Whitelist is subnet
        ("2001:db8::/32", "2002:db8::/32", Relation.DIFFERENT),  # Different networks
        ("2001:db8:1:2::/64", "2001:db8::/32", Relation.SUPERNET),  # Whitelist is supernet
    ],
)
def test_check_whitelist_to_rule_relation(rule, whitelist, expected):
    clear_network_cache()
    assert check_whitelist_to_rule_relation(rule, whitelist) == expected


@pytest.mark.parametrize(
    "target,whitelist,expected",
    [
        # Basic IPv4 cases
        (
            "192.168.1.0/24",
            "192.168.1.128/25",
            ["192.168.1.0/25"],
        ),  # One remaining subnet
        (
            "192.168.1.0/24",
            "192.168.1.64/26",
            ["192.168.1.0/26", "192.168.1.128/25"],
        ),  # Two remaining subnets
        (
            "192.168.1.0/24",
            "192.168.1.0/24",
            ["192.168.1.0/24"],
        ),  # Equal networks - return original network
        (
            "192.168.1.0/24",
            "192.168.2.0/24",
            ["192.168.1.0/24"],
        ),  # No overlap
    ],
)
def test_subtract_network(target, whitelist, expected):
    clear_network_cache()
    result = subtract_network(target, whitelist)
    assert sorted(result) == sorted(expected)


def test_check_rule_against_whitelists():
    clear_network_cache()

    rule = "192.168.1.0/24"
    whitelists = [
        "192.168.0.0/16",  # SUPERNET
        "172.16.0.0/12",  # DIFFERENT
        "192.168.1.0/24",  # EQUAL
        "192.168.1.128/25",  # SUBNET
    ]

    results = check_rule_against_whitelists(rule, whitelists)

    # Should return list of tuples (rule, whitelist, relation) for non-DIFFERENT relations
    expected = [
        (rule, "192.168.0.0/16", Relation.SUPERNET),
        (rule, "192.168.1.0/24", Relation.EQUAL),
        (rule, "192.168.1.128/25", Relation.SUBNET),
    ]

    assert len(results) == 3
    for result, exp in zip(sorted(results), sorted(expected)):
        assert result == exp


def test_check_whitelist_against_rules():
    clear_network_cache()

    whitelist = "192.168.1.128/25"
    rules = [
        "192.168.0.0/16",  # Whitelist is SUBNET of this larger network
        "172.16.0.0/12",  # DIFFERENT
        "192.168.1.128/25",  # EQUAL
        "192.168.1.0/24",  # Whitelist is SUBNET of this network
    ]

    results = check_whitelist_against_rules(rules, whitelist)

    # Should return list of tuples (rule, whitelist, relation) for non-DIFFERENT relations
    expected = [
        ("192.168.0.0/16", whitelist, Relation.SUBNET),
        ("192.168.1.128/25", whitelist, Relation.EQUAL),
        ("192.168.1.0/24", whitelist, Relation.SUBNET),
    ]

    assert len(results) == 3
    for result, exp in zip(sorted(results), sorted(expected)):
        assert result == exp


# Tests for edge cases and error handling
def test_host_addresses():
    clear_network_cache()
    # Test with host addresses (no explicit subnet mask)
    assert check_whitelist_to_rule_relation("192.168.1.1", "192.168.1.0/24") == Relation.SUPERNET
    assert check_whitelist_to_rule_relation("192.168.1.1", "192.168.2.0/24") == Relation.DIFFERENT


def test_single_ip_as_network():
    clear_network_cache()
    # Test with /32 (single IPv4 address as network)
    assert check_whitelist_to_rule_relation("192.168.1.1/32", "192.168.1.0/24") == Relation.SUPERNET
    # Test with /128 (single IPv6 address as network)
    assert check_whitelist_to_rule_relation("2001:db8::1/128", "2001:db8::/32") == Relation.SUPERNET


def test_invalid_input():
    clear_network_cache()
    with pytest.raises(ValueError):
        check_whitelist_to_rule_relation("invalid", "192.168.1.0/24")

    with pytest.raises(ValueError):
        check_whitelist_to_rule_relation("192.168.1.0/24", "invalid")

    with pytest.raises(ValueError):
        subtract_network("invalid", "192.168.1.0/24")


if __name__ == "__main__":
    pytest.main(["-v"])
