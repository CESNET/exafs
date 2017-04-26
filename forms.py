from flask_wtf import FlaskForm
from wtforms import TextField, SelectMultipleField
from wtforms.validators import DataRequired, EqualTo, Length, Email, ValidationError
from models import User



class Unique(object):
    """ validator that checks field uniqueness """
    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'this element already exists'
        self.message = message

    def __call__(self, form, field):         
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)    
    

class UserForm(FlaskForm):
    
    email = TextField(
        'Email', validators=[DataRequired("Required field"), 
                            Email("Please provide valid email"),
                            Unique(User, User.email)]
    )

    role_ids = SelectMultipleField(u'Role',
        coerce=int,
        validators=[DataRequired("Select at last one role")])

    org_ids = SelectMultipleField(u'Organization',
        coerce=int,
        validators=[DataRequired("Select at last one Organization")])


