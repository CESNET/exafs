from datetime import datetime
from flask import flash

def webpicker_to_datetime(webtime):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.strptime(webtime, '%m/%d/%Y %H:%M')


def datetime_to_webpicker(python_time):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.strftime(python_time, '%m/%d/%Y %H:%M')


def flash_errors(form):
    """
    Flash all error messages
    :param form: WTForm object
    :return: none
    """
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ))
