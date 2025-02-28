"""
API key forms for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, HiddenField
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
