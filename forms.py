from flask_wtf import FlaskForm
from wtforms import TextField, SelectMultipleField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, Email, IPAddress, NumberRange, Optional, ValidationError
import flowspec

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
        validators=[Optional()]
    )


class ActionForm(FlaskForm):
    
    name = TextField(
        'Action short name',
        validators=[Optional(), Length(max=150)]
    )

    description = TextField('Action description')


class IPv4Form(FlaskForm):

    source_adress = TextField('Source address',
        validators=[Optional(), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )

    source_mask = IntegerField('Source mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    destination_adress = TextField('Destination address',
        validators=[Optional(),  IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )
    
    destination_mask = IntegerField('Destination mask (bytes)',
        validators=[Optional(), NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    protocol = SelectMultipleField('Protocol',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[Optional(), DataRequired("Select at last one protocol")])

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