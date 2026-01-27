import pytest
from datetime import datetime, timedelta
from werkzeug.datastructures import MultiDict
from flowapp.forms import (
    UserForm,
    BulkUserForm,
    ApiKeyForm,
    MachineApiKeyForm,
    OrganizationForm,
    ActionForm,
    ASPathForm,
    CommunityForm,
    RTBHForm,
    IPv4Form,
    IPv6Form,
    WhitelistForm,
)


def create_form_data(data):
    """Helper function to create proper form data format"""
    processed_data = {}
    for key, value in data.items():
        if isinstance(value, list):
            processed_data[key] = [str(v) for v in value]
        else:
            processed_data[key] = value
    return MultiDict(processed_data)


@pytest.fixture
def valid_datetime():
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")


@pytest.fixture
def sample_network_ranges():
    return ["192.168.0.0/16", "2001:db8::/32"]


class TestUserForm:
    @pytest.fixture
    def mock_choices(self):
        return {
            "role_ids": [(1, "Admin"), (2, "User"), (3, "Guest")],
            "org_ids": [(1, "Org1"), (2, "Org2"), (3, "Org3")],
        }

    @pytest.fixture
    def valid_user_data(self):
        return {
            "uuid": "test@example.com",
            "email": "user@example.com",
            "name": "Test User",
            "phone": "123456789",
            "role_ids": ["2"],
            "org_ids": ["1"],
        }

    def test_valid_user_form(self, app, valid_user_data, mock_choices):
        with app.test_request_context():
            form_data = create_form_data(valid_user_data)
            form = UserForm(formdata=form_data)
            form.role_ids.choices = mock_choices["role_ids"]
            form.org_ids.choices = mock_choices["org_ids"]

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_invalid_email(self, app, mock_choices):
        with app.test_request_context():
            form_data = create_form_data({"uuid": "invalid-email", "role_ids": ["2"], "org_ids": ["1"]})
            form = UserForm(formdata=form_data)
            form.role_ids.choices = mock_choices["role_ids"]
            form.org_ids.choices = mock_choices["org_ids"]

            assert not form.validate()
            assert "Please provide valid email" in form.uuid.errors


class TestRTBHForm:
    @pytest.fixture
    def mock_community_choices(self):
        return [(1, "Community1"), (2, "Community2")]

    @pytest.fixture
    def valid_rtbh_data(self, valid_datetime):
        return {
            "ipv4": "192.168.1.0",
            "ipv4_mask": 24,
            "community": "1",
            "expires": valid_datetime,
            "comment": "Test RTBH rule",
        }

    def test_valid_ipv4_rtbh(self, app, valid_rtbh_data, sample_network_ranges, mock_community_choices):
        with app.test_request_context():
            form_data = create_form_data(valid_rtbh_data)
            form = RTBHForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.community.choices = mock_community_choices
            assert form.validate()


class TestIPv4Form:
    @pytest.fixture
    def mock_action_choices(self):
        return [(1, "Accept"), (2, "Drop"), (3, "Reject")]

    @pytest.fixture
    def valid_ipv4_data(self, valid_datetime):
        return {
            "source": "192.168.1.0",
            "source_mask": "24",
            "protocol": "tcp",
            "action": "1",
            "expires": valid_datetime,
        }

    def test_valid_ipv4_rule(self, app, valid_ipv4_data, sample_network_ranges, mock_action_choices):
        with app.test_request_context():
            form_data = create_form_data(valid_ipv4_data)
            form = IPv4Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_invalid_protocol_flags(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "192.168.1.0",
                    "source_mask": "24",
                    "protocol": "udp",
                    "flags": ["syn"],
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv4Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices
            assert not form.validate()


class TestIPv6Form:
    @pytest.fixture
    def mock_action_choices(self):
        return [(1, "Accept"), (2, "Drop"), (3, "Reject")]

    @pytest.fixture
    def valid_ipv6_data(self, valid_datetime):
        return {
            "source": "2001:db8::",  # Network aligned address within allowed range
            "source_mask": "32",  # Matching the organization's prefix length
            "next_header": "tcp",
            "action": "1",
            "expires": valid_datetime,
        }

    def test_valid_ipv6_rule(self, app, valid_ipv6_data, sample_network_ranges, mock_action_choices):
        with app.test_request_context():
            form_data = create_form_data(valid_ipv6_data)
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_invalid_next_header_flags(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "2001:db8::",
                    "source_mask": "32",
                    "next_header": "udp",
                    "flags": ["syn"],
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices
            assert not form.validate()

    def test_address_outside_range(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        """Test validation fails when address is outside allowed ranges"""
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "2001:db9::",  # Different prefix
                    "source_mask": "32",
                    "next_header": "tcp",
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices
            assert not form.validate()
            assert any("must be in organization range" in error for error in form.source.errors)

    def test_destination_address(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        """Test validation with destination address instead of source"""
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "dest": "2001:db8::",
                    "dest_mask": "32",
                    "next_header": "tcp",
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_both_source_and_dest(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        """Test validation with both source and destination addresses"""
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "2001:db8::",
                    "source_mask": "32",
                    "dest": "2001:db8:1::",
                    "dest_mask": "48",
                    "next_header": "tcp",
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_tcp_flags(self, app, valid_datetime, sample_network_ranges, mock_action_choices):
        """Test validation with TCP flags (should be valid with TCP)"""
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "2001:db8::",
                    "source_mask": "32",
                    "next_header": "tcp",
                    "flags": ["SYN", "ACK"],
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    @pytest.mark.parametrize("port_data", ["80", "80;443", "1024-2048"])
    def test_valid_ports(self, app, valid_datetime, sample_network_ranges, mock_action_choices, port_data):
        """Test validation with various valid port formats"""
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "source": "2001:db8::",
                    "source_mask": "32",
                    "next_header": "tcp",
                    "source_port": port_data,
                    "dest_port": port_data,
                    "action": "1",
                    "expires": valid_datetime,
                }
            )
            form = IPv6Form(formdata=form_data)
            form.net_ranges = sample_network_ranges
            form.action.choices = mock_action_choices

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()


class TestBulkUserForm:
    @pytest.fixture
    def valid_csv_data(self):
        return "uuid-eppn,role,organizace\nuser1@example.com,2,1\nuser2@example.com,2,1"

    def test_valid_bulk_import(self, app, valid_csv_data):
        with app.test_request_context():
            form_data = create_form_data({"users": valid_csv_data})
            form = BulkUserForm(formdata=form_data)
            form.roles = {2}  # Mock available roles
            form.organizations = {1}  # Mock available organizations
            form.uuids = set()  # Mock existing UUIDs (empty set)
            assert form.validate()

    def test_duplicate_uuid(self, app, valid_csv_data):
        with app.test_request_context():
            form_data = create_form_data({"users": valid_csv_data})
            form = BulkUserForm(formdata=form_data)
            form.roles = {2}
            form.organizations = {1}
            form.uuids = {"user1@example.com"}  # UUID already exists
            assert not form.validate()
            assert any("already exists" in error for error in form.users.errors)

    def test_invalid_role(self, app):
        csv_data = "uuid-eppn,role,organizace\nuser1@example.com,999,1"  # Invalid role ID
        with app.test_request_context():
            form_data = create_form_data({"users": csv_data})
            form = BulkUserForm(formdata=form_data)
            form.roles = {2}
            form.organizations = {1}
            form.uuids = set()
            assert not form.validate()
            assert any("does not exist" in error for error in form.users.errors)


class TestApiKeyForm:
    @pytest.fixture
    def valid_api_key_data(self, valid_datetime):
        return {"machine": "192.168.1.1", "comment": "Test API key", "expires": valid_datetime, "readonly": "true"}

    def test_valid_api_key(self, app, valid_api_key_data):
        with app.test_request_context():
            form_data = create_form_data(valid_api_key_data)
            form = ApiKeyForm(formdata=form_data)
            assert form.validate()

    def test_invalid_ip(self, app, valid_datetime):
        with app.test_request_context():
            form_data = create_form_data({"machine": "invalid_ip", "expires": valid_datetime})
            form = ApiKeyForm(formdata=form_data)
            assert not form.validate()
            assert "provide valid IP address" in form.machine.errors

    def test_unlimited_expiration(self, app):
        with app.test_request_context():
            form_data = create_form_data({"machine": "192.168.1.1", "expires": ""})  # Empty expiration for unlimited
            form = ApiKeyForm(formdata=form_data)
            assert form.validate()


class TestMachineApiKeyForm:
    # Similar to ApiKeyForm, but might have different validation rules
    @pytest.fixture
    def valid_machine_key_data(self, valid_datetime):
        return {
            "machine": "192.168.1.1",
            "comment": "Test machine API key",
            "expires": valid_datetime,
            "readonly": "true",
            "user": 1,
        }

    def test_valid_machine_key(self, app, valid_machine_key_data):
        with app.test_request_context():
            form_data = create_form_data(valid_machine_key_data)
            form = MachineApiKeyForm(formdata=form_data)
            form.user.choices = [(1, "g.name"), (2, "test")]
            assert form.validate()


class TestOrganizationForm:
    @pytest.fixture
    def valid_org_data(self):
        return {
            "name": "Test Organization",
            "limit_flowspec4": "100",
            "limit_flowspec6": "100",
            "limit_rtbh": "50",
            "arange": "192.168.0.0/16\n2001:db8::/32",
        }

    def test_valid_organization(self, app, valid_org_data):
        with app.test_request_context():
            form_data = create_form_data(valid_org_data)
            form = OrganizationForm(formdata=form_data)
            assert form.validate()

    def test_invalid_ranges(self, app):
        with app.test_request_context():
            form_data = create_form_data({"name": "Test Org", "arange": "invalid_range\n192.168.0.0/16"})
            form = OrganizationForm(formdata=form_data)
            assert not form.validate()

    def test_invalid_limits(self, app):
        with app.test_request_context():
            form_data = create_form_data({"name": "Test Org", "limit_flowspec4": "1001"})  # Exceeds max value
            form = OrganizationForm(formdata=form_data)
            assert not form.validate()


class TestActionForm:
    @pytest.fixture
    def valid_action_data(self):
        return {
            "name": "test_action",
            "command": "announce route",
            "description": "Test action description",
            "role_id": "2",
        }

    def test_valid_action(self, app, valid_action_data):
        with app.test_request_context():
            form_data = create_form_data(valid_action_data)
            form = ActionForm(formdata=form_data)
            assert form.validate()

    def test_invalid_role(self, app, valid_action_data):
        with app.test_request_context():
            invalid_data = dict(valid_action_data)
            invalid_data["role_id"] = "4"  # Invalid role
            form_data = create_form_data(invalid_data)
            form = ActionForm(formdata=form_data)
            assert not form.validate()


class TestASPathForm:
    @pytest.fixture
    def valid_aspath_data(self):
        return {"prefix": "AS64512", "as_path": "64512 64513 64514"}

    def test_valid_aspath(self, app, valid_aspath_data):
        with app.test_request_context():
            form_data = create_form_data(valid_aspath_data)
            form = ASPathForm(formdata=form_data)
            assert form.validate()

    def test_empty_fields(self, app):
        with app.test_request_context():
            form_data = create_form_data({})
            form = ASPathForm(formdata=form_data)
            assert not form.validate()


class TestCommunityForm:
    @pytest.fixture
    def valid_community_data(self):
        return {
            "name": "test_community",
            "comm": "64512:100",
            "description": "Test community",
            "role_id": "2",
            "as_path": "true",
        }

    def test_valid_community(self, app, valid_community_data):
        with app.test_request_context():
            form_data = create_form_data(valid_community_data)
            form = CommunityForm(formdata=form_data)
            assert form.validate()

    def test_missing_all_community_types(self, app):
        with app.test_request_context():
            form_data = create_form_data({"name": "test_community", "role_id": "2"})
            form = CommunityForm(formdata=form_data)
            assert not form.validate()
            assert any("could not be empty" in error for error in form.comm.errors)

    def test_valid_with_extended_community(self, app):
        with app.test_request_context():
            form_data = create_form_data({"name": "test_community", "extcomm": "rt:64512:100", "role_id": "2"})
            form = CommunityForm(formdata=form_data)
            assert form.validate()

    def test_valid_with_large_community(self, app):
        with app.test_request_context():
            form_data = create_form_data({"name": "test_community", "larcomm": "64512:100:200", "role_id": "2"})
            form = CommunityForm(formdata=form_data)
            assert form.validate()


class TestWhitelistForm:
    @pytest.fixture
    def valid_ipv4_data(self, valid_datetime):
        return {"ip": "192.168.0.0", "mask": "24", "comment": "Test whitelist entry", "expires": valid_datetime}

    @pytest.fixture
    def valid_ipv6_data(self, valid_datetime):
        return {"ip": "2001:db8::", "mask": "32", "comment": "IPv6 whitelist entry", "expires": valid_datetime}

    def test_valid_ipv4_entry(self, app, valid_ipv4_data, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data(valid_ipv4_data)
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_valid_ipv6_entry(self, app, valid_ipv6_data, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data(valid_ipv6_data)
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges

            if not form.validate():
                print("Validation errors:", form.errors)

            assert form.validate()

    def test_invalid_ip_format(self, app, valid_datetime, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data({"ip": "invalid_ip", "mask": "24", "expires": valid_datetime})
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()
            assert any("valid IP address" in error for error in form.ip.errors)

    def test_ip_outside_range(self, app, valid_datetime):
        with app.test_request_context():
            form_data = create_form_data(
                {"ip": "10.0.0.0", "mask": "24", "expires": valid_datetime}  # IP outside allowed range
            )
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = ["192.168.0.0/16"]  # Only allow 192.168.0.0/16
            assert not form.validate()
            assert any("must be in organization range" in error for error in form.ip.errors)

    def test_invalid_mask_ipv4(self, app, valid_datetime, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data(
                {"ip": "192.168.0.0", "mask": "33", "expires": valid_datetime}  # Invalid mask for IPv4
            )
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()

    def test_invalid_mask_ipv6(self, app, valid_datetime, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data(
                {"ip": "2001:db8::", "mask": "129", "expires": valid_datetime}  # Invalid mask for IPv6
            )
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()

    def test_missing_required_fields(self, app, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data({})
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()
            assert form.ip.errors  # Should have error for missing IP
            assert form.mask.errors  # Should have error for missing mask
            assert form.expires.errors  # Should have error for missing expiration

    def test_comment_length(self, app, valid_datetime, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data(
                {
                    "ip": "192.168.0.0",
                    "mask": "24",
                    "expires": valid_datetime,
                    "comment": "x" * 256,  # Comment longer than 255 chars
                }
            )
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()

    @pytest.mark.parametrize(
        "expires", ["", "invalid_date", "2020-33-42T00:00"]  # Empty expiration  # Invalid date format  # Past date
    )
    def test_invalid_expiration(self, app, expires, sample_network_ranges):
        with app.test_request_context():
            form_data = create_form_data({"ip": "192.168.0.0", "mask": "24", "expires": expires})
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            if not form.validate():
                print("Validation errors:", form.errors)

            assert not form.validate()

    def test_network_alignment(self, app, valid_datetime, sample_network_ranges):
        """Test that IP addresses must be properly network-aligned"""
        with app.test_request_context():
            form_data = create_form_data(
                {"ip": "192.168.1.1", "mask": "24", "expires": valid_datetime}  # Not aligned to /24 boundary
            )
            form = WhitelistForm(formdata=form_data)
            form.net_ranges = sample_network_ranges
            assert not form.validate()
