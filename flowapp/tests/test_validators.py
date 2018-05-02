import pytest
import flowapp.validators


class FieldMock():

    def __init__(self):
        self.data = "tbd"


class RuleMock():

    def __init__(self):
        self.source = None
        self.source_mask = None
        self.dest = None
        self.dest_mask = None


@pytest.fixture
def field():
    return FieldMock()


@pytest.fixture
def rule():
    return RuleMock()


@pytest.mark.parametrize("address, mask, expected", [
    ("147.230.23.25", "24", False),
    ("147.230.23.0", "24", True),
    ("2001:718:1C01:1111::1111", "64", False),
    ("2001:718:1C01:1111::", "64", True),
])
def test_is_valid_address_with_mask(address, mask, expected):
    assert flowapp.validators.address_with_mask(address, mask) == expected


@pytest.mark.parametrize("address", [
    u"147.230.23.25",
    u"147.230.23.0",
    u"2001:718:1C01:1111::1111",
    u"2001:718:1C01:1111::",
])
def test_ipaddress_passes(field, address):
    adr = flowapp.validators.IPAddress()
    field.data = address
    adr(None, field)


@pytest.mark.parametrize("address", [
    u"147.230.1000.25",
    u"2001:718::::",
])
def test_ipaddress_raises(field, address):
    adr = flowapp.validators.IPAddress()
    field.data = address
    with pytest.raises(flowapp.validators.ValidationError):
        adr(None, field)


@pytest.mark.parametrize("address, mask, ranges, expected", [
    (u"147.230.23.0", u"24", [u"147.230.0.0/16", u"147.251.0.0/16"], True),
    (u"147.230.23.0", u"24", [u"147.230.0.0/16", u"147.251.0.0/16"], True)
])
def test_editable_rule(rule, address, mask, ranges, expected):
    rule.source = address
    rule.source_mask = mask
    assert flowapp.validators.editable_range(rule, ranges) == expected