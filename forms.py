from flask_wtf import FlaskForm
from wtforms import TextField, SelectMultipleField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, EqualTo, Length, Email, IPAddress, NumberRange


    
class UserForm(FlaskForm):
    
    email = TextField(
        'Email', validators=[DataRequired("Required field"), 
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
        validators=[DataRequired("Required field"), Length(max=150)]
    )

    arange = TextAreaField('Organization Adress Range - comma separated', 
        validators=[DataRequired("Required field")]
    )


class ActionForm(FlaskForm):
    
    name = TextField(
        'Action short name',
        validators=[DataRequired("Required field"), Length(max=150)]
    )

    description = TextField('Action description')


class IPv4Form(FlaskForm):

    source_adress = TextField('Source address',
        validators=[DataRequired("Required field"), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )

    source_mask = IntegerField('Source mask (bytes)',
        validators=[NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    destination_adress = TextField('Destination address',
        validators=[DataRequired("Required field"), IPAddress(ipv4=True, ipv6=False, message='provide valid IPv4 adress')]
    )
    
    destination_mask = IntegerField('Destination mask (bytes)',
        validators=[NumberRange(min=0, max=255, message='invalid mask value (0-255)')])

    protocol = SelectMultipleField('Protocol',
        choices=[('tcp', 'TCP'), ('udp', 'UDP'), ('icmp', 'ICMP')],
        validators=[DataRequired("Select at last one protocol")])

    source_port = TextField(
        'Source port(s) - comma separated',
        validators=[DataRequired("Required field"), Length(max=255)]
    )

    destination_port  = TextField(
        'Destination port(s) - comma separated',
        validators=[DataRequired("Required field"), Length(max=255)]
    )


    packet_length = IntegerField('Packet length')
    
    action = SelectField(u'Action',
        coerce=int,
        validators=[DataRequired()])

    
    expire_date = TextField(
        'Expires'
    )
    
    comment = arange = TextAreaField('Comments'
    )