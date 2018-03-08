import datetime
from flask import flash


def webpicker_to_datetime(webtime):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.datetime.strptime(webtime, '%m/%d/%Y %H:%M')


def datetime_to_webpicker(python_time):
    """
    convert 'MM/DD/YYYY HH:mm' to datetime
    """
    return datetime.datetime.strftime(python_time, '%m/%d/%Y %H:%M')


def round_to_ten_minutes(python_time):
    """
    Round given time to nearest ten minutes
    :param python_time: datetime
    :return: datetime
    """
    python_time += datetime.timedelta(minutes=5)
    python_time -= datetime.timedelta(minutes=python_time.minute % 10,
                             seconds=python_time.second,
                             microseconds=python_time.microsecond)

    return python_time


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
