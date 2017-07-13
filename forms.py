from flask_wtf import FlaskForm
from wtforms import TextField, SelectMultipleField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, Email, IPAddress, NumberRange, Optional, ValidationError, Required
import flowspec
import ipaddress

TCP_FLAGS = [('SYN', 'SYN'), ('ACK', 'ACK'),('FIN', 'FIN'),('URG', 'URG'),('PSH', 'PSH'),('RST', 'RST'),('ECE', 'ECE'),('CWR', 'CWR'),('NS', 'NS')]


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
    
    email = TextField(
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
    
    name = TextField(
        'Organization name',
        validators=[Optional(), Length(max=150)]
    )

    arange = TextAreaField('Organization Adress Range - one range per row', 
        validators=[Optional(), NetRageString()]
    )


class ActionForm(FlaskForm):
    
    name = TextField(
        'Action short name',
        validators=[Length(max=150)]
    )

    command = TextField(
        'ExaBGP command',
        validators=[Length(max=150)]
    )

    description = TextField('Action description')


class RTBHForm(FlaskForm):
    
    ipv4 = TextField('Source IPv4 address',
        validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )

    ipv4_mask = IntegerField('Source IPv4  mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    ipv6 = TextField('Source IPv6 address',
        validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
    )
    ipv6_mask = IntegerField('Source mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    expires = TextField(
        'Expires'
    )

    comment = arange = TextAreaField('Comments'
    )

   
class IPv4Form(FlaskForm):
    
    def __init__(self, *args, **kwargs):
        super(IPv4Form, self).__init__(*args, **kwargs)
        self.net_ranges = None

    source = TextField('Source address',
        validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )

    source_mask = IntegerField('Source mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    dest = TextField('Destination address',
        validators=[Optional(),  IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )
    
    dest_mask = IntegerField('Destination mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    protocol = SelectField('Protocol(s)',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[Required()])

    flags = SelectMultipleField('TCP flag(s)',
        choices=TCP_FLAGS,
        validators=[Optional()])

    source_port = TextField(
        'Source port(s) -  ; separated ',
        validators=[Optional(), Length(max=255), PortString()]
    )

    dest_port  = TextField(
        'Destination port(s) - ; separated',
        validators=[Optional(), Length(max=255), PortString()]
    )


    packet_len = TextField('Packet length',  validators=[Optional(), Length(max=255), PacketString()])
    
    action = SelectField(u'Action',
        coerce=int,
        validators=[DataRequired()])

    
    expires = TextField(
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
    
    source = TextField('Source address',
        validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
    )

    source_mask = IntegerField('Source prefix length (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    dest = TextField('Destination address',
        validators=[Optional(),  IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
    )
    
    dest_mask = IntegerField('Destination prefix length (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    next_header = SelectField('Next Header',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[Required()])

    flags = SelectMultipleField('TCP flag(s)',
        choices=TCP_FLAGS,
        validators=[Optional()])


    source_port = TextField(
        'Source port(s) -  ; separated ',
        validators=[Optional(), Length(max=255), PortString()]
    )

    dest_port  = TextField(
        'Destination port(s) - ; separated',
        validators=[Optional(), Length(max=255), PortString()]
    )


    packet_len = TextField('Packet length',  validators=[Optional(), Length(max=255)])
    
    action = SelectField(u'Action',
        coerce=int,
        validators=[DataRequired()])

    
    expires = TextField(
        'Expires'
    )
    
    comment = arange = TextAreaField('Comments'
    )    



def add_adress_range_validator(form, net_ranges):
    """
    add validator to instance but only once                             
    """
    source_exist = False
    for val in form.source.validators:
        if type(val) is NetInRange:
            source_exist = True

    if not source_exist:
        form.source.validators.append(NetInRange(net_ranges))

    dest_exist = False
    for val in form.dest.validators:
        if type(val) is NetInRange:
            source_exist = True
    

    if len(form.dest.validators) == 2:
        form.dest.validators.append(NetInRange(net_ranges))    

    return form          