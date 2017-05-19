from flask_wtf import FlaskForm
from wtforms import TextField, SelectMultipleField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, Email, IPAddress, NumberRange, Optional, ValidationError
import flowspec
import ipaddress

TCP_FLAGS = [('ACK', 'ACK'),('FIN', 'FIN'),('URG', 'URG'),('PSH', 'PSH'),('RST', 'RST'),('ECE', 'ECE'),('CWR', 'CWR'),('NS', 'NS')]


class PortString(object):
    def __init__(self, message=None):
        if not message:
            message = u'Invalid port value: '
        self.message = message

    def __call__(self, form, field):
        try:
            for port_string in field.data.split(";"):
                flowspec.translate_port_string(port_string)
        except ValueError, e:
            raise ValidationError(self.message + str(e.args[0]))


class NetRageString(object):
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
    def __init__(self, net_ranges):
        self.message = "address not in organization range"
        self.net_ranges = net_ranges

    def __call__(self, form, field):
        result = False
        for address in field.data.split("/"):
            for adr_range in self.net_ranges:
                result = result or ipaddress.ip_address(address) in ipaddress.ip_network(adr_range)
                print "RESULT RANGE: ", result
        
        if result == False:
            raise ValidationError(self.message)

    
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
        validators=[Optional(), Length(max=150)]
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

    expire_date = TextField(
        'Expires'
    )

    comment = arange = TextAreaField('Comments'
    )

   
class IPv4Form(FlaskForm):
    
    source = TextField('Source address',
        validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )

    source_mask = IntegerField('Source mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    destination = TextField('Destination address',
        validators=[Optional(),  IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )
    
    destination_mask = IntegerField('Destination mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    protocol = SelectMultipleField('Protocol(s)',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[Optional()])

    flags = SelectMultipleField('TCP flag(s)',
        choices=TCP_FLAGS,
        validators=[Optional()])


    protocol_string = TextField(
        'Protocols',
        validators=[Optional(), Length(max=255), PortString()]
    )

    source_port = TextField(
        'Source port(s) -  ; separated ',
        validators=[Optional(), Length(max=255), PortString()]
    )

    destination_port  = TextField(
        'Destination port(s) - ; separated',
        validators=[Optional(), Length(max=255), PortString()]
    )


    packet_length = TextField('Packet length',  validators=[Optional(), Length(max=255)])
    
    action = SelectField(u'Action',
        coerce=int,
        validators=[DataRequired()])

    
    expire_date = TextField(
        'Expires'
    )
    
    comment = arange = TextAreaField('Comments'
    )


class IPv6Form(FlaskForm):
    
    source = TextField('Source address',
        validators=[Optional(), IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
    )

    source_mask = IntegerField('Source mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    destination = TextField('Destination address',
        validators=[Optional(),  IPAddress(ipv6=True, ipv4=False, message='provide valid IPv6 adress')]
    )
    
    destination_mask = IntegerField('Destination mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    next_header = SelectMultipleField('Next Header',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[Optional()])

    flags = SelectMultipleField('TCP flag(s)',
        choices=TCP_FLAGS,
        validators=[Optional()])


    next_header_string = TextField(
        'Next Header',
        validators=[Optional(), Length(max=255), PortString()]
    )

    source_port = TextField(
        'Source port(s) -  ; separated ',
        validators=[Optional(), Length(max=255), PortString()]
    )

    destination_port  = TextField(
        'Destination port(s) - ; separated',
        validators=[Optional(), Length(max=255), PortString()]
    )


    packet_length = TextField('Packet length',  validators=[Optional(), Length(max=255)])
    
    action = SelectField(u'Action',
        coerce=int,
        validators=[DataRequired()])

    
    expire_date = TextField(
        'Expires'
    )
    
    comment = arange = TextAreaField('Comments'
    )    



def add_adress_range_validator(form, net_ranges):
    """
    add validator to instance but only once                             
    """
    if len(form.source.validators) == 2:
        form.source.validators.append(NetInRange(net_ranges))
    if len(form.destination.validators) == 2:
        form.destination.validators.append(NetInRange(net_ranges))    

    return form          