import pytest
import flowapp.forms


@pytest.fixture()
def ip_form(app, field_class):
    with app.test_request_context():  # Push the request context
        form = flowapp.forms.IPForm()
        form.source = field_class()
        form.dest = field_class()
        form.source_mask = field_class()
        form.dest_mask = field_class()
        return form


def test_ip_form_created(ip_form):
    assert ip_form.source.data is None
    assert ip_form.source.errors == []


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
def test_ip_form_validate_source_address(ip_form, address, mask, expected):
    ip_form.source.data = address
    ip_form.source_mask.data = mask
    assert ip_form.validate_source_address() == expected


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
def test_ip_form_validate_dest_address(ip_form, address, mask, expected):
    ip_form.dest.data = address
    ip_form.dest_mask.data = mask
    assert ip_form.validate_dest_address() == expected


@pytest.mark.parametrize(
    "address, mask, ranges, expected",
    [
        ("147.230.23.0", "24", ["147.230.0.0/16", "2001:718:1c01::/48"], True),
        ("0.0.0.0", "0", ["147.230.0.0/16", "2001:718:1c01::/48"], False),
        ("195.113.0.0", "16", ["195.113.0.0/18", "195.113.64.0/21"], False),
    ],
)
def test_ip_form_validate_address_mask(ip_form, address, mask, ranges, expected):
    ip_form.net_ranges = ranges
    ip_form.source.data = address
    ip_form.source_mask.data = mask
    assert ip_form.validate_address_ranges() == expected
