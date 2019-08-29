from operator import ge, lt
from datetime import datetime, timedelta
from flask import flash


def quote_to_ent(comment):
    """
    Convert all " to &quot;
    Used for comment sanitize / because of tooltip in dashboard break when quotes are unescaped
    :param comment: string to be sanitized
    :return: string
    """
    return comment.replace('"', '&quot;')


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


def get_state_by_time(python_time):
    """
    returns state for rule based on given time
    if given time is in the past returns 2 (withdrawed rule)
    else returns 1
    :param python_time:
    :return: integer rstate
    """
    present = datetime.now()

    if python_time <= present:
        return 2
    else:
        return 1


def round_to_ten_minutes(python_time):
    """
    Round given time to nearest ten minutes
    :param python_time: datetime
    :return: datetime
    """
    python_time += timedelta(minutes=5)
    python_time -= timedelta(minutes=python_time.minute % 10,
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


def active_css_rstate(rtype, rstate):
    """
    returns dict with rstates as keys and css class value
    :param rstate: string
    :return: dict
    """

    return {'active': '', 'expired': '', 'all': '', 'ipv4': '', 'ipv6': '', 'rtbh': '', rtype: 'active',
            rstate: 'active'}


def get_comp_func(rstate='active'):
    comp_funcs = {
        'active': ge,
        'expired': lt,
        'all': None
    }

    try:
        comp_func = comp_funcs[rstate]
    except IndexError:
        comp_func = None
    except KeyError:
        comp_func = None

    return comp_func
