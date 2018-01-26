from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, IPAddress, NumberRange, Optional, ValidationError
import flowspec
import ipaddress

TCP_FLAGS = [('SYN', 'SYN'), ('ACK', 'ACK'), ('FIN', 'FIN'), ('URG', 'URG'), ('PSH', 'PSH'), ('RST', 'RST'),
             ('ECE', 'ECE'), ('CWR', 'CWR'), ('NS', 'NS')]


class PortString(object):
    """
    Validator for port string - must be translatable to ExaBgp syntax
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid port value: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.to_exabgp_string(port_string, flowspec.MAX_PORT)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class PacketString(object):
    """
    Validator for packet length string - must be translatable to ExaBgp syntax
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid packet size value: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.to_exabgp_string(port_string, flowspec.MAX_PACKET)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class NetRageString(object):
    """
    Validator for  IP adress network range
    each part of string must be valid ip address separated by spaces, newlines
    """

    def __init__(self, message=None):
        if not message:
            message = u'Invalid network range: '
        self.message = message

    def __call__(self, form, field):
        try:
            for net_string in field.data.split():
                _a = ipaddress.ip_network(net_string)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class NetInRange(object):
    """
    Validator for IP address - must be in organization net range
    """

    def __init__(self, net_ranges):
        self.message = "Address not in organization range : {}.".format(net_ranges)
        self.net_ranges = net_ranges

    def __call__(self, form, field):
        result = False
        for address in field.data.split("/"):
            for adr_range in self.net_ranges:
                result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)

        if result == False:
            raise ValidationError(self.message)


def address_in_range(address, address_range):
    result = False
    try:
        for adr_range in address_range:
            result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)
    except ValueError:
        result = False

    return result


class UserForm(FlaskForm):
    email = StringField(
        'Email', validators=[Optional(),
                             Email("Please provide valid email")]
    )

    role_ids = SelectMultipleField(u'Role',
                                   coerce=int,
                                   validators=[DataRequired("Select at last one role")])

    org_ids = SelectMultipleField(u'Organization',
                                  coerce=int,
                                  validators=[DataRequired("Select at last one Organization")])


class OrganizationForm(FlaskForm):
    name = StringField(
        'Organization name',
        validators=[Optional(), Length(max=150)]
    )

    arange = TextAreaField('Organization Adress Range - one range per row',
                           validators=[Optional(), NetRageString()]
                           )


class ActionForm(FlaskForm):
    name = StringField(
        'Action short name',
        validators=[Length(max=150)]
    )

    command = StringField(
        'ExaBGP command',
        validators=[Length(max=150)]
    )

    description = StringField('Action description')


class RTBHForm(FlaskForm):
    ipv4 = StringField('Source IPv4 address',
                       validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
                       )

    ipv4_mask = IntegerField('Source IPv4  mask (bytes)',
                             validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    ipv6 = StringField('Source IPv6 address',
                       validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
                       )
    ipv6_mask = IntegerField('Source mask (bytes)',
                             validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    community = SelectField('Community',
                            choices=[('2852:666', '2852:666'), ('40965:666', '40965:666'), ('xxxxx:666', 'xxxxx:666')],
                            validators=[DataRequired()])

    expires = StringField(
        'Expires'
    )

    comment = arange = TextAreaField('Comments'
                                     )


class IPv4Form(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(IPv4Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    source = StringField('Source address',
                         validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
                         )

    source_mask = IntegerField('Source mask (bytes)',
                               validators=[Optional(), NumberRange(min=0, max=32, message='invalid mask value (0-32)')])

    dest = StringField('Destination address',
                       validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
                       )

    dest_mask = IntegerField('Destination mask (bytes)',
                             validators=[Optional(), NumberRange(min=0, max=32, message='invalid mask value (0-32)')])

    protocol = SelectField('Protocol',
                           choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
                           validators=[DataRequired()])

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

    packet_len = StringField('Packet length', validators=[Optional(), Length(max=255), PacketString()])

    action = SelectField(u'Action',
                         coerce=int,
                         validators=[DataRequired()])

    expires = StringField(
        'Expires'
    )

    comment = arange = TextAreaField('Comments'
                                     )

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        source_in_range = address_in_range(self.source.data, self.net_ranges)
        dest_in_range = address_in_range(self.dest.data, self.net_ranges)

        if not (source_in_range or dest_in_range):
            self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
            self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
            return False

        if len(self.flags.data) > 0 and self.protocol.data != 'tcp':
            self.flags.errors.append("Can not set TCP flags for protocol {} !".format(self.protocol.data.upper()))
            return False

        return True


class IPv6Form(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(IPv6Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    source = StringField('Source address',
                         validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
                         )

    source_mask = IntegerField('Source prefix length (bytes)',
                               validators=[Optional(),
                                           NumberRange(min=64, max=128, message='invalid prefix value (64-128)')])

    dest = StringField('Destination address',
                       validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
                       )

    dest_mask = IntegerField('Destination prefix length (bytes)',
                             validators=[Optional(),
                                         NumberRange(min=64, max=128, message='invalid prefix value (64-128)')])

    next_header = SelectField('Next Header',
                              choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
                              validators=[DataRequired()])

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

    packet_len = StringField('Packet length', validators=[Optional(), Length(max=255)])

    action = SelectField(u'Action',
                         coerce=int,
                         validators=[DataRequired()])

    expires = StringField(
        'Expires'
    )

    comment = arange = TextAreaField('Comments'
                                     )

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        source_in_range = address_in_range(self.source.data, self.net_ranges)
        dest_in_range = address_in_range(self.dest.data, self.net_ranges)

        if not (source_in_range or dest_in_range):
            self.source.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
            self.dest.errors.append("Source or dest must be in organization range : {}.".format(self.net_ranges))
            return False

        if len(self.flags.data) > 0 and self.next_header.data != 'tcp':
            self.flags.errors.append("Can not set TCP flags for next-header {} !".format(self.protocol.data.upper()))
            return False

        return True
