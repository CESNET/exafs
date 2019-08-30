from datetime import datetime

import jwt
from flask import Blueprint, render_template, redirect, flash, request, url_for, session, make_response

from flowapp import auth_required, constants, models, app, active_css_rstate, validators, db, flowspec

dashboard = Blueprint('dashboard', __name__, template_folder='templates')


@dashboard.route('/<path:rtype>/<path:rstate>/')
@auth_required
def index(rtype='ipv4', rstate='active'):

    get_sort_key = request.args.get(constants.SORT_ARG) if request.args.get(
        constants.SORT_ARG) else constants.DEFAULT_SORT
    get_sort_order = request.args.get(constants.ORDER_ARG) if request.args.get(
        constants.ORDER_ARG) else constants.DEFAULT_ORDER

    # store current state for redirects
    session[constants.ORDER_ARG] = get_sort_order
    session[constants.SORT_ARG] = get_sort_key
    session[constants.RULE_ARG] = rstate
    session[constants.TYPE_ARG] = rtype
    # switch order when click on the same column twice
    try:
        if session[constants.SORT_ARG] == get_sort_key:
            get_sort_order = 'desc' if get_sort_order == 'asc' else 'asc'
    except KeyError:
        get_sort_order = constants.DEFAULT_ORDER

    rules = models.get_ip_rules(rtype, rstate, get_sort_key, get_sort_order)

    if 3 in session['user_role_ids']:
        res, encoded = create_admin_responose(rtype, rstate, rules, get_sort_key, get_sort_order)

    else:
        res, encoded = create_user_response(rtype, rstate, rules, get_sort_key, get_sort_order)

    if app.config.get('DEVEL'):
        res.set_cookie(constants.RULES_KEY, encoded, httponly=True, samesite='Lax')
    else:
        res.set_cookie(constants.RULES_KEY, encoded, secure=True, httponly=True, samesite='Lax')

    return res


def create_admin_responose(rtype, rstate, rules, sort_key, sort_order):
    """
    Admin can see and edit any rules
    :param rtype:
    :param rstate:
    :param rules:
    :param all_actions:
    :param sort_order:
    :return:
    """

    rule_type_dispatch = {
        'ipv4': {
            'title': 'IPv4 rules',
            'columns': constants.RULES_COLUMNS_V4
        },
        'ipv6': {
            'title': 'IPv6 rules',
            'columns': constants.RULES_COLUMNS_V6
        },
        'rtbh': {
            'title': 'RTBH rules',
            'columns': constants.RTBH_COLUMNS
        }
    }

    res = make_response(render_template('pages/dashboard_admin.j2',
                                        rules=rules,
                                        table_title=rule_type_dispatch[rtype]['title'],
                                        rules_columns=rule_type_dispatch[rtype]['columns'],
                                        css_classes=active_css_rstate(rtype, rstate),
                                        sort_order=sort_order,
                                        sort_key=sort_key,
                                        rstate=rstate,
                                        rtype=rtype,
                                        rtype_int=constants.RULE_TYPES[rtype],
                                        today=datetime.now()))

    encoded = create_jwt_payload(rules, rtype)

    return res, encoded


def create_user_response(rtype, rstate, rules, sort_key, sort_order):
    """
    Filter out the rules for normal users
    :param rules:
    :param rstate:
    :return:
    """
    rule_type_dispatch = {
        'ipv4': {
            'title': 'IPv4 rules',
            'columns': constants.RULES_COLUMNS_V4
        },
        'ipv6': {
            'title': 'IPv6 rules',
            'columns': constants.RULES_COLUMNS_V6
        },
        'rtbh': {
            'title': 'RTBH rules',
            'columns': constants.RTBH_COLUMNS
        }
    }

    net_ranges = models.get_user_nets(session['user_id'])

    if rtype == 'rtbh':
        rules_editable = validators.filter_rtbh_rules(net_ranges, rules)
        rules_visible = []
    else:
        rules = validators.filter_rules_in_network(net_ranges, rules)
        user_actions = models.get_user_actions(session['user_role_ids'])
        user_actions = [act[0] for act in user_actions]
        rules_editable, rules_visible = flowspec.filter_rules_action(user_actions, rules)

    res = make_response(render_template('pages/dashboard_user.j2',
                                        table_title=rule_type_dispatch[rtype]['title'],
                                        rules_columns=rule_type_dispatch[rtype]['columns'],
                                        rules_editable=rules_editable,
                                        rules_visible=rules_visible,
                                        css_classes=active_css_rstate(rtype, rstate),
                                        sort_order=sort_order,
                                        sort_key=sort_key,
                                        rstate=rstate,
                                        rtype=rtype,
                                        rtype_int=constants.RULE_TYPES[rtype],
                                        today=datetime.now()))

    encoded = create_jwt_payload(rules_editable, rtype)

    return res, encoded


def create_jwt_payload(rules, rtype):
    jwt_key = app.config.get('JWT_SECRET')

    payload = {
        constants.RULE_TYPES[rtype]: [rule.id for rule in rules]
    }

    encoded = jwt.encode(payload, jwt_key, algorithm='HS256')

    return encoded