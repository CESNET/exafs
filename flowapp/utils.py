from operator import ge, lt
from datetime import datetime, timedelta
from flask import flash
from flowapp.constants import COMP_FUNCS


def output_date_format(json_request_data, pref_format='yearfirst'):
    """
    prefer user setting from parameter, if the parameter is not set
    then use the prefered format computed from input date
    """
    if "time_format" in json_request_data and json_request_data["time_format"]:
        return json_request_data["time_format"]
    else:
        return pref_format


def parse_api_time(apitime):
    """
    check if the api time is in US, EU or timestamp format
    :param apitime: string with date and time
    :returns: datetime, prefered format
    """
    try:
        return round_to_ten_minutes(webpicker_to_datetime(apitime)), "yearfirst"
    except ValueError:
        mytime = False

    try:
        return round_to_ten_minutes(webpicker_to_datetime(apitime, 'us')), "us"
    except ValueError:
        mytime = False

    try:
        return round_to_ten_minutes(datetime.fromtimestamp(int(apitime))), "timestamp"
    except OverflowError:
        mytime = False
    except ValueError:
        mytime = False

    return False             


def quote_to_ent(comment):
    """
    Convert all " to &quot;
    Used for comment sanitize / because of tooltip in dashboard break when quotes are unescaped
    :param comment: string to be sanitized
    :return: string
    """
    return comment.replace('"', '&quot;')


def webpicker_to_datetime(webtime, format='yearfirst'):
    """
    convert 'YYYY/MM/DD HH:mm' to datetime
    """
    if format=='yearfirst':
        formating_string = '%Y/%m/%d %H:%M'
    else:
        formating_string = '%m/%d/%Y %H:%M'

    return datetime.strptime(webtime, formating_string)


def datetime_to_webpicker(python_time, format='yearfirst'):
    """
    convert datetime to 'YYYY/MM/DD HH:mm' string
    """
    if format=='yearfirst':
        formating_string = '%Y/%m/%d %H:%M'
    else:
        formating_string = '%m/%d/%Y %H:%M'

    return datetime.strftime(python_time, formating_string)


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

    try:
        comp_func = COMP_FUNCS[rstate]
    except IndexError:
        comp_func = None
    except KeyError:
        comp_func = None

    return comp_func
