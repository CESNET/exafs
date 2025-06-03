"""
User-related forms for the flowapp application.
"""

import csv
from io import StringIO

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectMultipleField
from wtforms.validators import ValidationError, DataRequired, Email, InputRequired, Optional


class UserForm(FlaskForm):
    """
    User Form object
    used in Admin
    """

    uuid = StringField(
        "Unique User ID",
        validators=[
            InputRequired("Please provide UUID"),
            Email("Please provide valid email"),
        ],
    )

    email = StringField("Email", validators=[Optional(), Email("Please provide valid email")])

    comment = StringField("Notice", validators=[Optional()])

    name = StringField("Name", validators=[Optional()])

    phone = StringField("Contact phone", validators=[Optional()])

    role_ids = SelectMultipleField("Role", coerce=int, validators=[DataRequired("Select at last one role")])

    org_ids = SelectMultipleField(
        "Organization",
        coerce=int,
        validators=[DataRequired("We prefer one Organization per user, but it's possible select more")],
    )


class BulkUserForm(FlaskForm):
    """
    Bulk User Form object
    used in Admin
    """

    users = TextAreaField("Users in CSV - see example below", validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(BulkUserForm, self).__init__(*args, **kwargs)
        self.roles = None
        self.organizations = None
        self.uuids = None

    # Custom validator for CSV data
    def validate_users(self, field):
        csv_data = field.data

        # Parse CSV data
        csv_reader = csv.DictReader(StringIO(csv_data), delimiter=",")

        # List to keep track of failed validation rows
        errors = 0
        for row_num, row in enumerate(csv_reader, start=1):
            try:
                # check if the user not already exists
                if row["uuid-eppn"] in self.uuids:
                    field.errors.append(f"Row {row_num}: User with UUID {row['uuid-eppn']} already exists.")
                    errors += 1

                # Check if role exists in the database
                role_id = int(row["role"])  # Convert role field to integer
                if role_id not in self.roles:
                    field.errors.append(f"Row {row_num}: Role ID {role_id} does not exist.")
                    errors += 1

                # Check if organization exists in the database
                org_id = int(row["organizace"])  # Convert organization field to integer
                if org_id not in self.organizations:
                    field.errors.append(f"Row {row_num}: Organization ID {org_id} does not exist.")
                    errors += 1

            except (KeyError, ValueError) as e:
                field.errors.append(f"Row {row_num}: Invalid data / key - {str(e)}. Check CSV head row.")

        if errors > 0:
            # Raise validation error if any invalid rows found
            raise ValidationError("Invalid CSV Data - check the errors above.")
