"""
API key forms for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, BooleanField, HiddenField
from wtforms.validators import DataRequired, IPAddress, Optional, Length

from .base import MultiFormatDateTimeLocalField
from ..constants import FORM_TIME_PATTERN


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
    ApiKey for Services / No login users.
    Each key / machine pair is unique
    This form is used by Admin to create api key for services or users with no Shibboleth login
    User must be created first and must have an organization
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

    readonly = BooleanField("Read only key", default=True)

    user = SelectField(
        "User",
        coerce=int,
        validators=[DataRequired("Select user")],
    )

    key = HiddenField("GeneratedKey")
