from flask import current_app
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeLocalField, HiddenField,
                     IntegerField, SelectField, SelectMultipleField,
                     StringField, TextAreaField)
from wtforms.validators import (DataRequired, Email, InputRequired, IPAddress,
                                Length, NumberRange, Optional)

from flowapp.constants import (IPV4_FRAGMENT, IPV4_PROTOCOL, IPV6_NEXT_HEADER,
                               TCP_FLAGS)
from flowapp.validators import (IPv4Address, IPv6Address, NetRangeString,
                                PortString, address_in_range,
                                address_with_mask, ipaddress, network_in_range,
                                whole_world_range)


class UserForm(FlaskForm):
    """
    User Form object
    used in Admin
    """
    uuid = StringField(
        'Unique User ID', validators=[InputRequired("Please provide UUID"),
                                      Email("Please provide valid email")]
    )

    email = StringField(
        'Email', validators=[Optional(),
                             Email("Please provide valid email")]
    )

    comment = StringField(
        'Notice', validators=[Optional()]
    )

    name = StringField(
        'Name', validators=[Optional()]
    )

    phone = StringField(
        'Contact phone', validators=[Optional()]
    )

    role_ids = SelectMultipleField(u'Role',
                                   coerce=int,
                                   validators=[DataRequired("Select at last one role")])

    org_ids = SelectMultipleField(u'Organization',
                                  coerce=int,
                                  validators=[DataRequired("Select at last one Organization")])


class ApiKeyForm(FlaskForm):
    """
    ApiKey for User
    Each key / machine pair is unique
    """
    machine = StringField('Machine address',
                          validators=[DataRequired(), IPAddress(message='provide valid IP address')]
                          )

    key = HiddenField("GeneratedKey")


class OrganizationForm(FlaskForm):
    """
    Organization form object
    used in Admin
    """
    name = StringField(
        'Organization name',
        validators=[Optional(), Length(max=150)]
    )

    arange = TextAreaField('Organization Adress Range - one range per row',
                           validators=[Optional(), NetRangeString()]
                           )


class ActionForm(FlaskForm):
    """
    Action form object
    used in Admin
    """
    name = StringField(
        'Action short name',
        validators=[Length(max=150)]
    )

    command = StringField(
        'ExaBGP command',
        validators=[Length(max=150)]
    )

    description = StringField('Action description')

    role_id = SelectField('Minimal required role',
                          choices=[('2', 'user'), ('3', 'admin')],
                          validators=[DataRequired()])


class ASPathForm(FlaskForm):
    """
    AS Path form object
    used in Admin
    """
    prefix = StringField(
        'Prefix',
        validators=[Length(max=120), DataRequired()]
    )

    as_path = StringField(
        'as-path value',
        validators=[Length(max=250), DataRequired()]
    )


class CommunityForm(FlaskForm):
    """
    Community form object
    used in Admin
    """
    name = StringField(
        'Community short name',
        validators=[Length(max=120), DataRequired()]
    )

    comm = StringField(
        'Community value',
        validators=[Length(max=2046)]
    )

    larcomm = StringField(
        'Large community value',
        validators=[Length(max=2046)]
    )

    extcomm = StringField(
        'Extended community value',
        validators=[Length(max=2046)]
    )

    description = StringField('Community description', validators=[Length(max=255)])

    role_id = SelectField('Minimal required role',
                          choices=[('2', 'user'), ('3', 'admin')],
                          validators=[DataRequired()])

    as_path = BooleanField('add AS-path (checked = true)')                      

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

    ipv4 = StringField('IPv4 address',
                       validators=[Optional(), IPv4Address(message='provide valid IPv4 adress')]
                       )

    ipv4_mask = IntegerField('IPv4  mask (bits)',
                             validators=[Optional(),
                                         NumberRange(min=0, max=32, message='invalid IPv4 mask value (0-32)')])

    ipv6 = StringField('IPv6 address',
                       validators=[Optional(), IPv6Address(message='provide valid IPv6 adress')]
                       )
    ipv6_mask = IntegerField('IPv6 mask (bits)',
                             validators=[Optional(),
                                         NumberRange(min=0, max=128, message='invalid IPv6 mask value (0-128)')])

    community = SelectField('Community',
                            coerce=int,
                            validators=[DataRequired(message="Please select a community for the rule."),])

    expires = StringField('Expires')

    comment = arange = TextAreaField('Comments'
                                     )

    def validate(self):
        """
        custom validation method
        :return: boolean
        """
        result = True

        if not FlaskForm.validate(self):
            result = False

        if self.ipv4.data and not address_with_mask(self.ipv4.data, self.ipv4_mask.data):
            self.ipv4.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv4.data,
                                                                                  self.ipv4_mask.data))
            result = False

        if self.ipv6.data and not address_with_mask(self.ipv6.data, self.ipv6_mask.data):
            self.ipv6.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.ipv6.data,
                                                                                  self.ipv6_mask.data))
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
    flags = SelectMultipleField('TCP flag(s)',
                                choices=TCP_FLAGS,
                                validators=[Optional()])

    source_port = StringField(
        'Source port(s) -  ; separated ',
        validators=[Optional(), Length(max=255), PortString()]
    )

    dest_port = StringField(
        'Destination port(s) - ; separated',
        validators=[Optional(), Length(max=255), PortString()]
    )

    packet_len = StringField(
        'Packet length - ; separated ',
        validators=[Optional(), Length(max=255), PortString()])

    action = SelectField(u'Action',
                         coerce=int,
                         validators=[DataRequired(message="Please select an action for the rule.")])

    expires = DateTimeLocalField('Expires',  format='%Y-%m-%dT%H:%M', validators=[InputRequired()])


    comment = arange = TextAreaField('Comments')

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
                "This is not valid combination of address {} and mask {}.".format(self.source.data,
                                                                                  self.source_mask.data))
            return False

        return True

    def validate_dest_address(self):
        """
        validate dest address, set error message if validation fails
        :return: boolean validation result
        """
        if self.dest.data and not address_with_mask(self.dest.data, self.dest_mask.data):
            self.dest.errors.append(
                "This is not valid combination of address {} and mask {}.".format(self.dest.data,
                                                                                  self.dest_mask.data))
            return False

        return True

    def validate_address_ranges(self):
        """
        validates if the address of source is in the user range
        if the source and dest address are empty, check if the user is member of whole world organization
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

    zero_address = u"0.0.0.0"
    source = StringField('Source address',
                         validators=[Optional(), IPv4Address(message='provide valid IPv4 adress')]
                         )

    source_mask = IntegerField('Source mask (bits)',
                               validators=[Optional(), NumberRange(min=0, max=32, message='invalid mask value (0-32)')])

    dest = StringField('Destination address',
                       validators=[Optional(), IPv4Address(message='provide valid IPv4 adress')]
                       )

    dest_mask = IntegerField('Destination mask (bits)',
                             validators=[Optional(), NumberRange(min=0, max=32, message='invalid mask value (0-32)')])

    protocol = SelectField('Protocol',
                           choices=[(pr, pr.upper()) for pr in IPV4_PROTOCOL.keys()],
                           validators=[DataRequired()])

    fragment = SelectMultipleField('Fragment',
                           choices=[(frv, frk.upper()) for frk, frv in IPV4_FRAGMENT.items()],
                           validators=[Optional()])                           

    def validate_ipv_specific(self):
        """
        validate protocol and flags, set error message if validation fails
        :return: boolean validation result
        """

        if len(self.flags.data) > 0 and self.protocol.data != 'tcp':
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

    zero_address = u"::"
    source = StringField('Source address',
                         validators=[Optional(), IPv6Address(message='provide valid IPv6 adress')]
                         )

    source_mask = IntegerField('Source prefix length (bits)',
                               validators=[Optional(),
                                           NumberRange(min=0, max=128, message='invalid prefix value (0-128)')])

    dest = StringField('Destination address',
                       validators=[Optional(), IPv6Address(message='provide valid IPv6 adress')]
                       )

    dest_mask = IntegerField('Destination prefix length (bits)',
                             validators=[Optional(),
                                         NumberRange(min=0, max=128, message='invalid prefix value (0-128)')])

    next_header = SelectField('Next Header',
                              choices=[(pr, pr.upper()) for pr in IPV6_NEXT_HEADER.keys()],
                              validators=[DataRequired()])

    def validate_ipv_specific(self):
        """
        validate next header and flags, set error message if validation fails
        :return: boolean validation result
        """
        if len(self.flags.data) > 0 and self.next_header.data != 'tcp':
            self.flags.errors.append("Can not set TCP flags for next-header {} !".format(self.protocol.data.upper()))
            return False

        return True
