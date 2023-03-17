import pytest
import flowapp.validators


def test_port_string_len_raises(field):
    port = flowapp.validators.PortString()
    field.data = "1;2;3;4;5;6;7;8"
    with pytest.raises(flowapp.validators.ValidationError):
        port(None, field)


@pytest.mark.parametrize(
    "address, mask, expected",
    [
        ("147.230.23.25", "24", False),
        ("147.230.23.0", "24", True),
        ("0.0.0.0", "0", True),
        ("2001:718:1C01:1111::1111", "64", False),
        ("2001:718:1C01:1111::", "64", True),
    ],
)
def test_is_valid_address_with_mask(address, mask, expected):
    assert flowapp.validators.address_with_mask(address, mask) == expected


@pytest.mark.parametrize("address", ["147.230.23.25", "147.230.23.0"])
def test_ip4address_passes(field, address):
    adr = flowapp.validators.IPv4Address()
    field.data = address
    adr(None, field)


@pytest.mark.parametrize(
    "address",
    [
        "2001:718:1C01:1111::1111",
        "2001:718:1C01:1111::",
    ],
)
def test_ip6address_passes(field, address):
    adr = flowapp.validators.IPv6Address()
    field.data = address
    adr(None, field)


@pytest.mark.parametrize(
    "address",
    [
        "2001:718:1C01:1111::1111",
        "2001:718:1C01:1111::",
    ],
)
def test_bad_ip6address_raises(field, address):
    adr = flowapp.validators.IPv4Address()
    field.data = address
    with pytest.raises(flowapp.validators.ValidationError):
        adr(None, field)


@pytest.mark.parametrize(
    "expired", ["2018/10/25 14:46", "2018/12/20 9:46", "2019/05/22 12:33"]
)
def test_expired_date_raises(field, expired):
    adr = flowapp.validators.DateNotExpired()
    field.data = expired
    with pytest.raises(flowapp.validators.ValidationError):
        adr(None, field)


@pytest.mark.parametrize(
    "address",
    [
        "147.230.1000.25",
        "2001:718::::",
    ],
)
def test_ipaddress_raises(field, address):
    adr = flowapp.validators.IPv6Address()
    field.data = address
    with pytest.raises(flowapp.validators.ValidationError):
        adr(None, field)


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("147.230.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], True),
        ("147.230.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], True),
    ],
)
def test_editable_rule(rule, address, mask, ranges, expected):
    rule.source = address
    rule.source_mask = mask
    assert flowapp.validators.editable_range(rule, ranges) == expected


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("147.230.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], True),
        ("147.233.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], False),
        ("147.230.23.0", "24", ["147.230.0.0/16", "2001:718:1c01::/48"], True),
        ("195.113.0.0", "16", ["0.0.0.0/0", "::/0"], True),
    ],
)
def test_address_in_range(address, mask, ranges, expected):
    assert flowapp.validators.address_in_range(address, ranges) == expected


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("147.230.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], True),
        ("147.233.23.0", "24", ["147.230.0.0/16", "147.251.0.0/16"], False),
        ("195.113.0.0", "16", ["195.113.0.0/18", "195.113.64.0/21"], False),
        ("195.113.0.0", "16", ["0.0.0.0/0", "::/0"], True),
        (
            "195.113.0.0",
            "16",
            ["147.230.0.0/16", "2001:718:1c01::/48", "0.0.0.0/0", "::/0"],
            True,
        ),
    ],
)
def test_network_in_range(address, mask, ranges, expected):
    assert flowapp.validators.network_in_range(address, mask, ranges) == expected


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("195.113.0.0", "16", ["147.230.0.0/16", "195.113.250.0/24"], True),
    ],
)
def test_range_in_network(address, mask, ranges, expected):
    assert flowapp.validators.range_in_network(address, mask, ranges) == expected
