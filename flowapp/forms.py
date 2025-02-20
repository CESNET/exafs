import csv
from io import StringIO


from flask_wtf import FlaskForm
from wtforms import widgets
from wtforms import (
    BooleanField,
    DateTimeField,
    HiddenField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    StringField,
    TextAreaField,
)
from wtforms.validators import (
    ValidationError,
    DataRequired,
    Email,
    InputRequired,
    IPAddress,
    Length,
    NumberRange,
    Optional,
)

from flowapp.constants import (
    IPV4_FRAGMENT,
    IPV4_PROTOCOL,
    IPV6_NEXT_HEADER,
    TCP_FLAGS,
    FORM_TIME_PATTERN,
)
from flowapp.validators import (
    IPAddressValidator,
    IPv4Address,
    IPv6Address,
    NetRangeString,
    NetworkValidator,
    PortString,
    address_in_range,
    address_with_mask,
    network_in_range,
    whole_world_range,
)

from flowapp.utils import parse_api_time


class MultiFormatDateTimeLocalField(DateTimeField):
    """
    Same as :class:`~wtforms.fields.DateTimeField`, but represents an
    ``<input type="datetime-local">``.

    Custom implementation uses default HTML5 format for parsing the field.
    It's possible to use multiple formats - used in API.

    """

    widget = widgets.DateTimeLocalInput()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        self.unlimited = kwargs.pop("unlimited", False)
        self.pref_format = None
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if not valuelist:
            return None
        # with unlimited field we do not need to parse the empty value
        if self.unlimited and len(valuelist) == 1 and len(valuelist[0]) == 0:
            self.data = None
            return None

        date_str = " ".join((str(val) for val in valuelist))
        result, pref_format = parse_api_time(date_str)
        if result:
            self.data = result
            self.pref_format = pref_format
        else:
            self.data = None
            self.pref_format = None
            raise ValueError(self.gettext("Not a valid datetime value."))


class UserForm(FlaskForm):
    """
    User Form object
    used in Admin
    """

    uuid = StringField(
        "Unique User ID",
        validators=[
            InputRequired("Please provide UUID"),
            Email("Please provide valid email"),
        ],
    )

    email = StringField("Email", validators=[Optional(), Email("Please provide valid email")])

    comment = StringField("Notice", validators=[Optional()])

    name = StringField("Name", validators=[Optional()])

    phone = StringField("Contact phone", validators=[Optional()])

    role_ids = SelectMultipleField("Role", coerce=int, validators=[DataRequired("Select at last one role")])

    org_ids = SelectMultipleField(
        "Organization",
        coerce=int,
        validators=[DataRequired("We prefer one Organization per user, but it's possible select more")],
    )


class BulkUserForm(FlaskForm):
    """
    Bulk User Form object
    used in Admin
    """

    users = TextAreaField("Users in CSV - see example below", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(BulkUserForm, self).__init__(*args, **kwargs)
        self.roles = None
        self.organizations = None
        self.uuids = None

    # Custom validator for CSV data
    def validate_users(self, field):
        csv_data = field.data

        # Parse CSV data
        csv_reader = csv.DictReader(StringIO(csv_data), delimiter=",")

        # List to keep track of failed validation rows
        errors = 0
        for row_num, row in enumerate(csv_reader, start=1):
            try:
                # check if the user not already exists
                if row["uuid-eppn"] in self.uuids:
                    field.errors.append(f"Row {row_num}: User with UUID {row['uuid-eppn']} already exists.")
                    errors += 1

                # Check if role exists in the database
                role_id = int(row["role"])  # Convert role field to integer
                if role_id not in self.roles:
                    field.errors.append(f"Row {row_num}: Role ID {role_id} does not exist.")
                    errors += 1

                # Check if organization exists in the database
                org_id = int(row["organizace"])  # Convert organization field to integer
                if org_id not in self.organizations:
                    field.errors.append(f"Row {row_num}: Organization ID {org_id} does not exist.")
                    errors += 1

            except (KeyError, ValueError) as e:
                field.errors.append(f"Row {row_num}: Invalid data / key - {str(e)}. Check CSV head row.")

        if errors > 0:
            # Raise validation error if any invalid rows found
            raise ValidationError("Invalid CSV Data - check the errors above.")


class ApiKeyForm(FlaskForm):
    """
    ApiKey for User
    Each key / machine pair is unique
    """

    machine = StringField(
        "Machine address",
        validators=[DataRequired(), IPAddress(message="provide valid IP address")],
    )

    comment = TextAreaField("Your comment for this key", validators=[Optional(), Length(max=255)])

    expires = MultiFormatDateTimeLocalField(
        "Key expiration. Leave blank for non expring key (not-recomended).",
        format=FORM_TIME_PATTERN,
        validators=[Optional()],
        unlimited=True,
    )

    readonly = BooleanField("Read only key", default=False)

    key = HiddenField("GeneratedKey")


class MachineApiKeyForm(FlaskForm):
    """
    ApiKey for Machines
    Each key / machine pair is unique
    Only Admin can create new these keys
    """

    machine = StringField(
        "Machine address",
        validators=[DataRequired(), IPAddress(message="provide valid IP address")],
    )

    comment = TextAreaField("Your comment for this key", validators=[Optional(), Length(max=255)])

    expires = MultiFormatDateTimeLocalField(
        "Key expiration. Leave blank for non expring key (not-recomended).",
        format=FORM_TIME_PATTERN,
        validators=[Optional()],
        unlimited=True,
    )

    readonly = BooleanField("Read only key", default=False)

    key = HiddenField("GeneratedKey")


class OrganizationForm(FlaskForm):
    """
    Organization form object
    used in Admin
    """

    name = StringField("Organization name", validators=[Optional(), Length(max=150)])

    limit_flowspec4 = IntegerField(
        "Maximum number of IPv4 rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    limit_flowspec6 = IntegerField(
        "Maximum number of IPv6 rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    limit_rtbh = IntegerField(
        "Maximum number of RTBH rules, 0 for unlimited",
        validators=[
            Optional(),
            NumberRange(min=0, max=1000, message="invalid mask value (0-1000)"),
        ],
    )

    arange = TextAreaField(
        "Organization Adress Range - one range per row",
        validators=[Optional(), NetRangeString()],
    )


class ActionForm(FlaskForm):
    """
    Action form object
    used in Admin
    """

    name = StringField("Action short name", validators=[Length(max=150)])

    command = StringField("ExaBGP command", validators=[Length(max=150)])

    description = StringField("Action description")

    role_id = SelectField(
        "Minimal required role",
        choices=[("2", "user"), ("3", "admin")],
        validators=[DataRequired()],
    )


class ASPathForm(FlaskForm):
    """
    AS Path form object
    used in Admin
    """

    prefix = StringField("Prefix", validators=[Length(max=120), DataRequired()])

    as_path = StringField("as-path value", validators=[Length(max=250), DataRequired()])


class CommunityForm(FlaskForm):
    """
    Community form object
    used in Admin
    """

    name = StringField("Community short name", validators=[Length(max=120), DataRequired()])

    comm = StringField("Community value", validators=[Length(max=2046)])

    larcomm = StringField("Large community value", validators=[Length(max=2046)])

    extcomm = StringField("Extended community value", validators=[Length(max=2046)])

    description = StringField("Community description", validators=[Length(max=255)])

    role_id = SelectField(
        "Minimal required role",
        choices=[("2", "user"), ("3", "admin")],
        validators=[DataRequired()],
    )

    as_path = BooleanField("add AS-path (checked = true)")

    def validate(self):
        """
        custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        if not self.comm.data and not self.extcomm.data and not self.larcomm.data:
            err_message = "At last one of those values could not be empty"
            self.comm.errors.append(err_message)
            self.larcomm.errors.append(err_message)
            self.extcomm.errors.append(err_message)
            result = False

        return result


class RTBHForm(FlaskForm):
    """
    RoadToBlackHole rule form
    """

    def __init__(self, *args, **kwargs):
        super(RTBHForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    ipv4 = StringField(
        "IPv4 address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    ipv4_mask = IntegerField(
        "IPv4  mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid IPv4 mask value (0-32)"),
        ],
    )

    ipv6 = StringField(
        "IPv6 address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    ipv6_mask = IntegerField(
        "IPv6 mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid IPv6 mask value (0-128)"),
        ],
    )

    community = SelectField(
        "Community",
        coerce=int,
        validators=[
            DataRequired(message="Please select a community for the rule."),
        ],
    )

    expires = MultiFormatDateTimeLocalField(
        "Expires",
        format=FORM_TIME_PATTERN,
        validators=[DataRequired(), InputRequired()],
    )

    comment = arange = TextAreaField("Comments")

    def validate(self):
        """
        custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        # ipv4 and ipv6 are mutually exclusive
        # if both are set, validation fails
        # if none is set, validation fails
        # if one is set, validation passes
        if self.ipv4.data and self.ipv6.data:
            self.ipv4.errors.append("IPv4 and IPv6 are mutually exclusive in RTBH rule.")
            self.ipv6.errors.append("IPv4 and IPv6 are mutually exclusive in RTBH rule.")
            result = False

        if self.ipv4.data and not address_with_mask(self.ipv4.data, self.ipv4_mask.data):
            self.ipv4.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv4.data, self.ipv4_mask.data)
            )
            result = False

        if self.ipv6.data and not address_with_mask(self.ipv6.data, self.ipv6_mask.data):
            self.ipv6.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv6.data, self.ipv6_mask.data)
            )
            result = False

        ipv6_in_range = address_in_range(self.ipv6.data, self.net_ranges)
        ipv4_in_range = address_in_range(self.ipv4.data, self.net_ranges)

        if not (ipv6_in_range or ipv4_in_range):
            self.ipv6.errors.append("IPv4 or IPv6 address must be in organization range : {}.".format(self.net_ranges))
            self.ipv4.errors.append("IPv4 or IPv6 address must be in organization range : {}.".format(self.net_ranges))
            result = False

        return result


class IPForm(FlaskForm):
    """
    Base class for IPv4 and IPv6 rules
    """

    def __init__(self, *args, **kwargs):
        super(IPForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = None
    source = None
    source_mask = None
    dest = None
    dest_mask = None
    flags = SelectMultipleField("TCP flag(s)", choices=TCP_FLAGS, validators=[Optional()])

    source_port = StringField(
        "Source port(s) -  ; separated ",
        validators=[Optional(), Length(max=255), PortString()],
    )

    dest_port = StringField(
        "Destination port(s) - ; separated",
        validators=[Optional(), Length(max=255), PortString()],
    )

    packet_len = StringField(
        "Packet length - ; separated ",
        validators=[Optional(), Length(max=255), PortString()],
    )

    action = SelectField(
        "Action",
        coerce=int,
        validators=[DataRequired(message="Please select an action for the rule.")],
    )

    expires = MultiFormatDateTimeLocalField("Expires", format="%Y-%m-%dT%H:%M", validators=[InputRequired()])

    comment = arange = TextAreaField("Comments")

    def validate(self):
        """
        custom validation method
        :return: boolean
        """

        result = True
        if not FlaskForm.validate(self):
            result = False

        source = self.validate_source_address()
        dest = self.validate_dest_address()
        ranges = self.validate_address_ranges()
        ips = self.validate_ipv_specific()

        return result and source and dest and ranges and ips

    def validate_source_address(self):
        """
        validate source address, set error message if validation fails
        :return: boolean validation result
        """
        if self.source.data and not address_with_mask(self.source.data, self.source_mask.data):
            self.source.errors.append(
                "This is not valid combination of address {} and mask {}.".format(
                    self.source.data, self.source_mask.data
                )
            )
            return False

        return True

    def validate_dest_address(self):
        """
        validate dest address, set error message if validation fails
        :return: boolean validation result
        """
        if self.dest.data and not address_with_mask(self.dest.data, self.dest_mask.data):
            self.dest.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.dest.data, self.dest_mask.data)
            )
            return False

        return True

    def validate_address_ranges(self):
        """
        validates if the address of source is in the user range
        if the source and dest address are empty, check if the user
        is member of whole world organization
        :return: boolean validation result
        """
        if not (self.source.data or self.dest.data):
            whole_world_member = whole_world_range(self.net_ranges, self.zero_address)
            if not whole_world_member:
                self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                return False
        else:
            source_in_range = network_in_range(self.source.data, self.source_mask.data, self.net_ranges)
            dest_in_range = network_in_range(self.dest.data, self.dest_mask.data, self.net_ranges)
            if not (source_in_range or dest_in_range):
                self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
                return False

        return True

    def validate_ipv_specific(self):
        """
        abstract method must be implemented in the subclass
        """
        pass


class IPv4Form(IPForm):
    """
    IPv4 form object
    """

    def __init__(self, *args, **kwargs):
        super(IPv4Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = "0.0.0.0"
    source = StringField(
        "Source address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    source_mask = IntegerField(
        "Source mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid mask value (0-32)"),
        ],
    )

    dest = StringField(
        "Destination address",
        validators=[Optional(), IPv4Address(message="provide valid IPv4 adress")],
    )

    dest_mask = IntegerField(
        "Destination mask (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=32, message="invalid mask value (0-32)"),
        ],
    )

    protocol = SelectField(
        "Protocol",
        choices=[(pr, pr.upper()) for pr in IPV4_PROTOCOL.keys()],
        validators=[DataRequired()],
    )

    fragment = SelectMultipleField(
        "Fragment",
        choices=[(frv, frk.upper()) for frk, frv in IPV4_FRAGMENT.items()],
        validators=[Optional()],
    )

    def validate_ipv_specific(self):
        """
        validate protocol and flags, set error message if validation fails
        :return: boolean validation result
        """

        if self.flags.data and self.protocol.data and len(self.flags.data) > 0 and self.protocol.data != "tcp":
            self.flags.errors.append("Can not set TCP flags for protocol {} !".format(self.protocol.data.upper()))
            return False
        return True


class IPv6Form(IPForm):
    """
    IPv6 form object
    """

    def __init__(self, *args, **kwargs):
        super(IPv6Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    zero_address = "::"
    source = StringField(
        "Source address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    source_mask = IntegerField(
        "Source prefix length (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid prefix value (0-128)"),
        ],
    )

    dest = StringField(
        "Destination address",
        validators=[Optional(), IPv6Address(message="provide valid IPv6 adress")],
    )

    dest_mask = IntegerField(
        "Destination prefix length (bits)",
        validators=[
            Optional(),
            NumberRange(min=0, max=128, message="invalid prefix value (0-128)"),
        ],
    )

    next_header = SelectField(
        "Next Header",
        choices=[(pr, pr.upper()) for pr in IPV6_NEXT_HEADER.keys()],
        validators=[DataRequired()],
    )

    def validate_ipv_specific(self):
        """
        validate next header and flags, set error message if validation fails
        :return: boolean validation result
        """
        if len(self.flags.data) > 0 and self.next_header.data != "tcp":
            self.flags.errors.append("Can not set TCP flags for next-header {} !".format(self.next_header.data.upper()))
            return False

        return True


class WhitelistForm(FlaskForm):
    """
    Whitelist form object
    Used for creating and editing whitelist entries
    Supports both IPv4 and IPv6 addresses
    """

    def __init__(self, *args, **kwargs):
        super(WhitelistForm, self).__init__(*args, **kwargs)
        self.net_ranges = None

    ip = StringField(
        "IP address",
        validators=[
            DataRequired(message="Please provide an IP address"),
            IPAddressValidator(message="Please provide a valid IP address: {}"),
            NetworkValidator(mask_field_name="mask"),
        ],
    )

    mask = IntegerField(
        "Network mask (bits)",
        validators=[
            DataRequired(message="Please provide a network mask"),
        ],
    )

    comment = TextAreaField("Comments", validators=[Optional(), Length(max=255)])

    expires = MultiFormatDateTimeLocalField(
        "Expires",
        format=FORM_TIME_PATTERN,
        validators=[DataRequired(), InputRequired()],
    )

    def validate(self):
        """
        Custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        # Validate IP is in organization range
        if self.ip.data and self.mask.data and self.net_ranges:
            ip_in_range = network_in_range(self.ip.data, self.mask.data, self.net_ranges)
            if not ip_in_range:
                self.ip.errors.append("IP address must be in organization range: {}.".format(self.net_ranges))
                result = False

        return result
