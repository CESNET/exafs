"""
Base form fields for the flowapp application.
"""

from wtforms import widgets
from wtforms.fields import DateTimeField
from ..utils import parse_api_time


class MultiFormatDateTimeLocalField(DateTimeField):
    """
    Same as :class:`~wtforms.fields.DateTimeField`, but represents an
    ``<input type="datetime-local">``.

    Custom implementation uses default HTML5 format for parsing the field.
    It's possible to use multiple formats - used in API.

    """

    widget = widgets.DateTimeLocalInput()

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%dT%H:%M")
        self.unlimited = kwargs.pop("unlimited", False)
        self.pref_format = None
        super().__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if not valuelist or (len(valuelist) == 1 and not valuelist[0]):
            return None

        # with unlimited field we do not need to parse the empty value
        if self.unlimited and len(valuelist) == 1 and len(valuelist[0]) == 0:
            self.data = None
            return None

        date_str = " ".join((str(val) for val in valuelist))

        try:
            result, pref_format = parse_api_time(date_str)
        except TypeError:
            raise ValueError(self.gettext("Not a valid datetime value."))

        if result:
            self.data = result
            self.pref_format = pref_format
        else:
            self.data = None
            self.pref_format = None
            raise ValueError(self.gettext("Not a valid datetime value."))
