"""
Action, ASPath, and Community forms for the flowapp application.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField
from wtforms.validators import Length, DataRequired


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
