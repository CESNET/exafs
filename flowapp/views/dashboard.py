from datetime import datetime

import jwt
from flask import Blueprint, render_template, redirect, flash, request, url_for, session, make_response

from flowapp import auth_required, constants, models, app, active_css_rstate, validators, db

dashboard = Blueprint('dashboard', __name__, template_folder='templates')


@dashboard.route('/<path:rtype>/<path:rstate>/')
@auth_required
def index(rtype='ipv4', rstate='active'):
    all_actions = db.session.query(models.Action).all()
    all_actions = {act.id: act for act in all_actions}

    get_sort_key = request.args.get(constants.SORT_ARG) if request.args.get(
        constants.SORT_ARG) else constants.DEFAULT_SORT
    get_sort_order = request.args.get(constants.ORDER_ARG) if request.args.get(
        constants.ORDER_ARG) else constants.DEFAULT_ORDER

    try:
        if session[constants.SORT_ARG] == get_sort_key:
            get_sort_order = 'desc' if get_sort_order == 'asc' else 'asc'
    except KeyError:
        get_sort_order = constants.DEFAULT_ORDER

    session[constants.SORT_ARG] = get_sort_key
    session[constants.ORDER_ARG] = get_sort_order
    session[constants.RULE_ARG] = rstate
    session[constants.TYPE_ARG] = rtype

    rules = models.get_ip_rules(rtype, rstate, get_sort_key, get_sort_order)

    if 3 in session['user_role_ids']:
        res, encoded = create_admin_responose(rtype, rstate, rules, all_actions, get_sort_order)

    else:
        res, encoded = create_user_response(rules, all_actions, rstate)

    if app.config.get('DEVEL'):
        res.set_cookie(constants.RULES_KEY, encoded, httponly=True, samesite='Lax')
    else:
        res.set_cookie(constants.RULES_KEY, encoded, secure=True, httponly=True, samesite='Lax')

    return res


def create_admin_responose(rtype, rstate, rules, all_actions, sort_order):
    """
    Admin can see and edit any rules
    :param rtype:
    :param rstate:
    :param rules:
    :param all_actions:
    :param sort_order:
    :return:
    """
    jwt_key = app.config.get('JWT_SECRET')

    payload = {
        constants.RULE_TYPES[rtype]: [rule.id for rule in rules]
    }

    rule_type_dispatch = {
        'ipv4': {
            'table': 'pages/dashboard_table_ip.j2',
            'title': 'IPv4 rules',
            'columns': constants.RULES_COLUMNS_V4
        },
        'ipv6': {
            'table': 'pages/dashboard_table_ip.j2',
            'title': 'IPv6 rules',
            'columns': constants.RULES_COLUMNS_V6
        },
        'rtbh': {
            'table': 'pages/dashboard_table_rtbh.j2',
            'title': 'RTBH rules',
            'columns': constants.RTBH_COLUMNS
        }
    }

    encoded = jwt.encode(payload, jwt_key, algorithm='HS256')
    res = make_response(render_template('pages/dashboard_admin.j2',
                                        rules=rules,
                                        table_title=rule_type_dispatch[rtype]['title'],
                                        rule_table_template=rule_type_dispatch[rtype]['table'],
                                        actions=all_actions,
                                        css_classes=active_css_rstate(rtype, rstate),
                                        sort_order=sort_order,
                                        rules_columns=rule_type_dispatch[rtype]['columns'],
                                        rstate=rstate,
                                        rtype=rtype,
                                        rtype_int=constants.RULE_TYPES[rtype],
                                        today=datetime.now()))

    return res, encoded


def create_user_response(rules, all_actions, rstate):
    """
    Filter out the rules for normal users
    :param rules:
    :param all_actions:
    :param rstate:
    :return:
    """
    jwt_key = app.config.get('JWT_SECRET')

    net_ranges = models.get_user_nets(session['user_id'])

    rules4 = validators.filter_rules_in_network(net_ranges, rules4)
    rules6 = validators.filter_rules_in_network(net_ranges, rules6)
    rules_rtbh = validators.filter_rtbh_rules(net_ranges, rules_rtbh)

    user_actions = models.get_user_actions(session['user_role_ids'])
    user_actions = [act[0] for act in user_actions]

    rules4_editable, rules4_visible = flowspec.filter_rules_action(user_actions, rules4)
    rules6_editable, rules6_visible = flowspec.filter_rules_action(user_actions, rules6)

    rules_editable = {4: rules4_editable, 6: rules6_editable}
    rules_visible = {4: rules4_visible, 6: rules6_visible}
    res = make_response(render_template('pages/dashboard_user.j2',
                                        rules_editable=rules_editable,
                                        rules_visible=rules_visible,
                                        css_classes=active_css_rstate(rstate),
                                        actions=all_actions,
                                        rstate=rstate,
                                        rules_rtbh=rules_rtbh,
                                        today=datetime.now()))
    payload = {
        4: [rule.id for rule in rules4_editable],
        6: [rule.id for rule in rules6_editable],
        1: [rule.id for rule in rules_rtbh]
    }
    encoded = jwt.encode(payload, jwt_key, algorithm='HS256')

    return res, encoded
