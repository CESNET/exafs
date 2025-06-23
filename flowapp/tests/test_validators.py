import pytest
from flowapp.validators import (
    PortString,
    PacketString,
    NetRangeString,
    NetInRange,
    IPAddress,
    IPAddressValidator,
    NetworkValidator,
    ValidationError,
    address_in_range,
    address_with_mask,
    IPv4Address,
    IPv6Address,
    DateNotExpired,
    editable_range,
    network_in_range,
    range_in_network,
)


def test_port_string_len_raises(field):
    port = PortString()
    field.data = "1;2;3;4;5;6;7;8"
    with pytest.raises(ValidationError):
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
    assert address_with_mask(address, mask) == expected


@pytest.mark.parametrize("address", ["147.230.23.25", "147.230.23.0"])
def test_ip4address_passes(field, address):
    adr = IPv4Address()
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
    adr = IPv6Address()
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
    adr = IPv4Address()
    field.data = address
    with pytest.raises(ValidationError):
        adr(None, field)


@pytest.mark.parametrize("expired", ["2018/10/25 14:46", "2018/12/20 9:46", "2019/05/22 12:33"])
def test_expired_date_raises(field, expired):
    adr = DateNotExpired()
    field.data = expired
    with pytest.raises(ValidationError):
        adr(None, field)


@pytest.mark.parametrize(
    "address",
    [
        "147.230.1000.25",
        "2001:718::::",
    ],
)
def test_ipaddress_raises(field, address):
    adr = IPv6Address()
    field.data = address
    with pytest.raises(ValidationError):
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
    assert editable_range(rule, ranges) == expected


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
    assert address_in_range(address, ranges) == expected


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
    assert network_in_range(address, mask, ranges) == expected


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("195.113.0.0", "16", ["147.230.0.0/16", "195.113.250.0/24"], True),
    ],
)
def test_range_in_network(address, mask, ranges, expected):
    assert range_in_network(address, mask, ranges) == expected


### new tests


# New tests for previously uncovered validators


# Tests for PortString validator syntax
@pytest.mark.parametrize(
    "port_data",
    [
        "80",  # Simple number
        "80-443",  # Range with hyphen
        ">=80&<=443",  # Explicit range
        ">80",  # Greater than
        ">=80",  # Greater than or equal
        "<443",  # Less than
        "<=443",  # Less than or equal
        "80;443;8080",  # Multiple port expressions
    ],
)
def test_port_string_valid_syntax(field, port_data):
    validator = PortString()
    field.data = port_data
    validator(None, field)  # Should not raise


@pytest.mark.parametrize(
    "invalid_port_data",
    [
        "80,443",  # Comma not supported, should use semicolon
        "80..443",  # Invalid range syntax (should be 80-443)
        ">65536",  # Port number too high
        "-1",  # Negative number
        "<-1",  # Port number too low
        ">=80<=443",  # Invalid range syntax (missing &)
        "!=80",  # Not equals not supported
        "abc",  # Non-numeric
        "80-",  # Incomplete range
        "-80",  # Invalid range
        "80&&443",  # Invalid operator
        "443-80",  # End less than start
        ">=443&<=80",  # End less than start in explicit range
        "0-65537",  # Range exceeding max
    ],
)
def test_port_string_invalid_syntax(field, invalid_port_data):
    validator = PortString()
    field.data = invalid_port_data
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for PacketString validator
@pytest.mark.parametrize(
    "packet_data",
    ["1500", ">1000", "<9000", "1000-1500", ">=1000&<=1500", "1500;9000"],  # Multiple packet size expressions
)
def test_packet_string_valid(field, packet_data):
    validator = PacketString()
    field.data = packet_data
    validator(None, field)  # Should not raise


@pytest.mark.parametrize(
    "invalid_packet_data",
    [
        "65536",  # Too large
        "-1",  # Negative
        "1500..",  # Invalid range syntax
        "abc",  # Non-numeric
        "!!1500",  # Invalid operator
        "1500-",  # Incomplete range
        "9000-1500",  # End less than start
    ],
)
def test_packet_string_invalid(field, invalid_packet_data):
    validator = PacketString()
    field.data = invalid_packet_data
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for NetRangeString validator
@pytest.mark.parametrize(
    "net_range",
    [
        "192.168.0.0/24",
        "10.0.0.0/8\n172.16.0.0/12",
        "2001:db8::/32",
        "192.168.0.0/24 10.0.0.0/8",
        "2001:db8::/32 2001:db8:1::/48",
    ],
)
def test_net_range_string_valid(field, net_range):
    validator = NetRangeString()
    field.data = net_range
    validator(None, field)  # Should not raise


@pytest.mark.parametrize(
    "invalid_net_range",
    [
        "192.168.0.0/33",  # Invalid mask
        "256.256.256.0/24",  # Invalid IP
        "2001:xyz::/32",  # Invalid IPv6
        "192.168.0.0/24/",  # Malformed
        "not-an-ip/24",  # Invalid format
    ],
)
def test_net_range_string_invalid(field, invalid_net_range):
    validator = NetRangeString()
    field.data = invalid_net_range
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for NetInRange validator
def test_net_in_range_valid(field):
    net_ranges = ["192.168.0.0/16", "10.0.0.0/8"]
    validator = NetInRange(net_ranges)
    field.data = "192.168.1.1/24"
    validator(None, field)  # Should not raise


def test_net_in_range_invalid(field):
    net_ranges = ["192.168.0.0/16", "10.0.0.0/8"]
    validator = NetInRange(net_ranges)
    field.data = "172.16.1.1/24"
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for base IPAddress validator
@pytest.mark.parametrize("ip_addr", ["192.168.1.1", "10.0.0.1", "2001:db8::1", "fe80::1"])
def test_ip_address_valid(field, ip_addr):
    validator = IPAddress()
    field.data = ip_addr
    validator(None, field)  # Should not raise


@pytest.mark.parametrize("invalid_ip", ["256.256.256.256", "2001:xyz::1", "not-an-ip", "192.168.1"])
def test_ip_address_invalid(field, invalid_ip):
    validator = IPAddress()
    field.data = invalid_ip
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for universal IPAddressValidator
@pytest.mark.parametrize("ip_addr", ["192.168.1.1", "2001:db8::1", "", None])  # Empty is allowed  # None is allowed
def test_ip_address_validator_valid(field, ip_addr):
    validator = IPAddressValidator()
    field.data = ip_addr
    validator(None, field)  # Should not raise


@pytest.mark.parametrize("invalid_ip", ["256.256.256.256", "2001:xyz::1", "not-an-ip"])
def test_ip_address_validator_invalid(field, invalid_ip):
    validator = IPAddressValidator()
    field.data = invalid_ip
    with pytest.raises(ValidationError):
        validator(None, field)


# Tests for NetworkValidator
class MockForm:
    def __init__(self, address, mask):
        self._fields = {"mask": type("MockField", (), {"data": mask})()}


@pytest.mark.parametrize(
    "address,mask",
    [
        ("192.168.0.0", "24"),
        ("10.0.0.0", "8"),
        ("2001:db8::", "32"),
        ("", None),  # Empty values should pass
        (None, None),  # None values should pass
    ],
)
def test_network_validator_valid(field, address, mask):
    validator = NetworkValidator("mask")
    field.data = address
    form = MockForm(address, mask)
    validator(form, field)  # Should not raise


@pytest.mark.parametrize(
    "address,mask",
    [
        ("192.168.1.1", "24"),  # Not a network address
        ("192.168.0.0", "33"),  # Invalid IPv4 mask
        ("2001:db8::", "129"),  # Invalid IPv6 mask
        ("256.256.256.0", "24"),  # Invalid IP
        ("2001:xyz::", "32"),  # Invalid IPv6
    ],
)
def test_network_validator_invalid(field, address, mask):
    validator = NetworkValidator("mask")
    field.data = address
    form = MockForm(address, mask)
    with pytest.raises(ValidationError):
        validator(form, field)
