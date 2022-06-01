# flowapp/views/admin.py
from datetime import datetime, timedelta
from operator import ge, lt
from typing import Any, Set

import requests
from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

from flowapp import app, constants, db, messages
from flowapp.auth import (admin_required, auth_required, localhost_only,
                          user_or_admin_required)
from flowapp.forms import IPv4Form, IPv6Form, RTBHForm
from flowapp.models import (RTBH, Action, Community, Flowspec4, Flowspec6,
                            get_ipv4_model_if_exists, get_ipv6_model_if_exists,
                            get_rtbh_model_if_exists, get_user_actions,
                            get_user_communities, get_user_nets,
                            insert_initial_communities)
from flowapp.output import (ROUTE_MODELS, RULE_TYPES, announce_route,
                            log_route, log_withdraw)
from flowapp.utils import (datetime_to_webpicker, flash_errors,
                           get_state_by_time, quote_to_ent,
                           round_to_ten_minutes, webpicker_to_datetime)

rules = Blueprint('rules', __name__, template_folder='templates')

DATA_MODELS = {1: RTBH, 4: Flowspec4, 6: Flowspec6}
DATA_MODELS_NAMED = {'rtbh': RTBH, 'ipv4': Flowspec4, 'ipv6': Flowspec6}
DATA_FORMS = {1: RTBHForm, 4: IPv4Form, 6: IPv6Form}
DATA_FORMS_NAMED = {'rtbh': RTBHForm, 'ipv4': IPv4Form, 'ipv6': IPv6Form}
DATA_TEMPLATES = {1: 'forms/rtbh_rule.j2', 4: 'forms/ipv4_rule.j2', 6: 'forms/ipv6_rule.j2'}
DATA_TABLES = {1: 'RTBH', 4: 'flowspec4', 6: 'flowspec6'}
DEFAULT_SORT = {1: 'ivp4', 4: 'source', 6: 'source'}


@rules.route('/reactivate/<int:rule_type>/<int:rule_id>', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def reactivate_rule(rule_type, rule_id):
    """
    Set new time for the rule of given type identified by id
    :param rule_type: string - type of rule
    :param rule_id: integer - id of the rule
    """
    model_name = DATA_MODELS[rule_type]
    form_name = DATA_FORMS[rule_type]

    model = db.session.query(model_name).get(rule_id)
    form = form_name(request.form, obj=model)
    form.net_ranges = get_user_nets(session['user_id'])

    if rule_type > 2:
        form.action.choices = [(g.id, g.name)
                               for g in db.session.query(Action).order_by('name')]
        form.action.data = model.action_id

    if rule_type == 1:
        form.community.choices = get_user_communities(session['user_role_ids'])
        form.community.data = model.community_id

    if rule_type == 4:
        form.protocol.data = model.protocol

    if rule_type == 6:
        form.next_header.data = model.next_header

    # do not need to validate - all is readonly
    if request.method == 'POST':
        # set new expiration date
        model.expires = round_to_ten_minutes(webpicker_to_datetime(form.expires.data))
        # set again the active state
        model.rstate_id = get_state_by_time(webpicker_to_datetime(form.expires.data))
        model.comment = form.comment.data
        db.session.commit()
        flash(u'Rule successfully updated', 'alert-success')

        route_model = ROUTE_MODELS[rule_type]

        if model.rstate_id == 1:
            # announce route
            route = route_model(model, constants.ANNOUNCE)
            announce_route(route)
            # log changes
            log_route(session['user_id'], model, rule_type, "{} / {}".format(session['user_email'], session['user_orgs']))
        else:
            # withdraw route
            route = route_model(model, constants.WITHDRAW)
            announce_route(route)
            # log changes
            log_withdraw(session['user_id'], route, rule_type, model.id, "{} / {}".format(session['user_email'], session['user_orgs']))

        return redirect(url_for('dashboard.index',
                                rtype=session[constants.TYPE_ARG],
                                rstate=session[constants.RULE_ARG],
                                sort=session[constants.SORT_ARG],
                                squery=session[constants.SEARCH_ARG],
                                order=session[constants.ORDER_ARG]))
    else:
        flash_errors(form)

    form.expires.data = datetime_to_webpicker(model.expires)
    for field in form:
        if field.name not in ['expires', 'csrf_token', 'comment']:
            field.render_kw = {'disabled': 'disabled'}

    action_url = url_for('rules.reactivate_rule', rule_type=rule_type, rule_id=rule_id)

    return render_template(DATA_TEMPLATES[rule_type], form=form, action_url=action_url, editing=True, title="Update")


@rules.route('/delete/<int:rule_type>/<int:rule_id>', methods=['GET'])
@auth_required
@user_or_admin_required
def delete_rule(rule_type, rule_id):
    """
    Delete rule with given id and type
    :param sort_key:
    :param filter_text:
    :param rstate:
    :param rule_type: string - type of rule to be deleted
    :param rule_id: integer - rule id
    """
    rules_dict = session[constants.RULES_KEY]
    rules = rules_dict[str(rule_type)]
    model_name = DATA_MODELS[rule_type]
    route_model = ROUTE_MODELS[rule_type]

    model = db.session.query(model_name).get(rule_id)
    if model.id in rules:
        # withdraw route
        route = route_model(model, constants.WITHDRAW)
        announce_route(route)

        log_withdraw(session['user_id'], route, rule_type, model.id, "{} / {}".format(session['user_email'], session['user_orgs']))

        # delete from db
        db.session.delete(model)
        db.session.commit()
        flash(u'Rule deleted', 'alert-success')

    else:
        flash(u'You can not delete this rule', 'alert-warning')

    return redirect(url_for('dashboard.index',
                            rtype=session[constants.TYPE_ARG],
                            rstate=session[constants.RULE_ARG],
                            sort=session[constants.SORT_ARG],
                            squery=session[constants.SEARCH_ARG],
                            order=session[constants.ORDER_ARG]))


@rules.route('/group-operation', methods=['POST'])
@auth_required
@user_or_admin_required
def group_operation():
    """
    Delete rules
    """
    dispatch = {
        'group-update': group_update,
        'group-delete': group_delete
    }

    try:
        return dispatch[request.form['action']]()
    except KeyError:
        flash(u'Key Error in action dispatching!', 'alert-danger')
        return redirect(url_for('dashboard.index',
                                rtype=session[constants.TYPE_ARG],
                                rstate=session[constants.RULE_ARG],
                                sort=session[constants.SORT_ARG],
                                squery=session[constants.SEARCH_ARG],
                                order=session[constants.ORDER_ARG]))


@rules.route('/group-delete', methods=['POST'])
@auth_required
@user_or_admin_required
def group_delete():
    """
    Delete rules
    """
    rules_dict = session[constants.RULES_KEY]
    rule_type = session[constants.TYPE_ARG]
    rules = [str(rule) for rule in rules_dict[str(constants.RULE_TYPES[rule_type])]]
    model_name = DATA_MODELS_NAMED[rule_type]
    rule_type_int = constants.RULE_TYPES[rule_type]
    route_model = ROUTE_MODELS[rule_type_int]

    to_delete = request.form.getlist('delete-id')

    if set(to_delete).issubset(set(rules)):
        for rule_id in to_delete:
            # withdraw route
            model = db.session.query(model_name).get(rule_id)
            route = route_model(model, constants.WITHDRAW)
            announce_route(route)

            log_withdraw(session['user_id'], route, rule_type, model.id, "{} / {}".format(session['user_email'], session['user_orgs']))

        db.session.query(model_name).filter(model_name.id.in_(to_delete)).delete(synchronize_session=False)
        db.session.commit()

        flash(u'Rules {} deleted'.format(to_delete), 'alert-success')
    else:
        flash(u'You can not delete rules {}'.format(to_delete), 'alert-warning')

    return redirect(url_for('dashboard.index',
                            rtype=session[constants.TYPE_ARG],
                            rstate=session[constants.RULE_ARG],
                            sort=session[constants.SORT_ARG],
                            squery=session[constants.SEARCH_ARG],
                            order=session[constants.ORDER_ARG]))


@rules.route('/group-edit', methods=['POST'])
@auth_required
@user_or_admin_required
def group_update():
    """
    update rules
    """
    rule_type = session[constants.TYPE_ARG]
    model_name = DATA_MODELS_NAMED[rule_type]
    form_name = DATA_FORMS_NAMED[rule_type]
    to_update = request.form.getlist('delete-id')
    rules_dict = session[constants.RULES_KEY]
    rule_type = session[constants.TYPE_ARG]
    rule_type_int = constants.RULE_TYPES[rule_type]
    rules = [str(rule) for rule in rules_dict[str(rule_type_int)]]

    # redirect bad request
    if not set(to_update).issubset(set(rules)):
        flash(u'You can edit these rules!', 'alert-danger')
        return redirect(url_for('dashboard.index',
                                rtype=session[constants.TYPE_ARG],
                                rstate=session[constants.RULE_ARG],
                                sort=session[constants.SORT_ARG],
                                squery=session[constants.SEARCH_ARG],
                                order=session[constants.ORDER_ARG]))

    # populate the form
    session['group-update'] = to_update
    form = form_name(request.form)
    form.net_ranges = get_user_nets(session['user_id'])
    if rule_type_int > 2:
        form.action.choices = [(g.id, g.name)
                               for g in db.session.query(Action).order_by('name')]
    if rule_type_int == 1:
        form.community.choices = get_user_communities(session['user_role_ids'])

    form.expires.data = datetime_to_webpicker(datetime.now())
    for field in form:
        if field.name not in ['expires', 'csrf_token', 'comment']:
            field.render_kw = {'disabled': 'disabled'}

    action_url = url_for('rules.group_update_save', rule_type=rule_type_int)

    return render_template(DATA_TEMPLATES[rule_type_int], form=form, action_url=action_url, editing=True,
                           title="Group Update")


@rules.route('/group-save-update/<int:rule_type>', methods=['POST'])
@auth_required
@user_or_admin_required
def group_update_save(rule_type):
    # redirect bad request
    try:
        to_update = session['group-update']
    except KeyError:
        return redirect(url_for('dashboard.index',
                                rtype=session[constants.TYPE_ARG],
                                rstate=session[constants.RULE_ARG],
                                sort=session[constants.SORT_ARG],
                                squery=session[constants.SEARCH_ARG],
                                order=session[constants.ORDER_ARG]))

    model_name = DATA_MODELS[rule_type]
    form_name = DATA_FORMS[rule_type]

    form = form_name(request.form)

    # set new expiration date
    expires = round_to_ten_minutes(webpicker_to_datetime(form.expires.data))
    # set state by time
    rstate_id = get_state_by_time(webpicker_to_datetime(form.expires.data))
    comment = form.comment.data
    route_model = ROUTE_MODELS[rule_type]

    for rule_id in to_update:
        # update record
        model = db.session.query(model_name).get(rule_id)
        model.expires = expires
        model.rstate_id = rstate_id
        model.comment = "{} {}".format(model.comment, comment)
        db.session.commit()

        if model.rstate_id == 1:
            # announce route
            route = route_model(model, constants.ANNOUNCE)
            announce_route(route)
            # log changes
            log_route(session['user_id'], model, rule_type, "{} / {}".format(session['user_email'], session['user_orgs']))
        else:
            # withdraw route
            route = route_model(model, constants.WITHDRAW)
            announce_route(route)
            # log changes
            log_withdraw(session['user_id'], route, rule_type, model.id, "{} / {}".format(session['user_email'], session['user_orgs']))

    flash(u'Rules {} successfully updated'.format(to_update), 'alert-success')

    return redirect(url_for('dashboard.index',
                            rtype=session[constants.TYPE_ARG],
                            rstate=session[constants.RULE_ARG],
                            sort=session[constants.SORT_ARG],
                            squery=session[constants.SEARCH_ARG],
                            order=session[constants.ORDER_ARG]))


@rules.route('/add_ipv4_rule', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def ipv4_rule():
    net_ranges = get_user_nets(session['user_id'])
    form = IPv4Form(request.form)

    # add values to form instance
    user_actions = get_user_actions(session['user_role_ids'])
    user_actions = [(0, '---- select action ----'),] + user_actions
    form.action.choices = user_actions
    form.action.default = 0
    form.net_ranges = net_ranges

    print("DEBUG", form.expires)
    print("DEBUG", dir(form.expires))
    print("DEBUG", form.expires.raw_data)
    print("DEBUG", form.expires.data)
    print("DEBUG", form.expires.strptime_format)
    print("DEBUG", form.expires.format)
    
    if request.method == 'POST' and form.validate():

        model = get_ipv4_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(webpicker_to_datetime(form.expires.data))
            flash_message = u'Existing IPv4 Rule found. Expiration time was updated to new value.'
        else:
            model = Flowspec4(
                source=form.source.data,
                source_mask=form.source_mask.data,
                source_port=form.source_port.data,
                destination=form.dest.data,
                destination_mask=form.dest_mask.data,
                destination_port=form.dest_port.data,
                protocol=form.protocol.data,
                flags=";".join(form.flags.data),
                packet_len=form.packet_len.data,
                fragment=";".join(form.fragment.data),
                expires=round_to_ten_minutes(form.expires.data),
                comment=quote_to_ent(form.comment.data),
                action_id=form.action.data,
                user_id=session['user_id'],
                rstate_id=get_state_by_time(form.expires.data)
            )
            flash_message = u'IPv4 Rule saved'
            db.session.add(model)

        db.session.commit()
        flash(flash_message, 'alert-success')

        # announce route if model is in active state
        if model.rstate_id == 1:
            route = messages.create_ipv4(model, constants.ANNOUNCE)
            announce_route(route)

        # log changes
        log_route(session['user_id'], model, RULE_TYPES['IPv4'], "{} / {}".format(session['user_email'], session['user_orgs']))

        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7)
    #form.expires.data = datetime_to_webpicker(default_expires)

    return render_template('forms/ipv4_rule.j2', form=form, action_url=url_for('rules.ipv4_rule'))


@rules.route('/add_ipv6_rule', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def ipv6_rule():
    net_ranges = get_user_nets(session['user_id'])
    form = IPv6Form(request.form)

    # set up form
    user_actions = get_user_actions(session['user_role_ids'])
    user_actions = [(0, '---- select action ----'),] + user_actions
    form.action.choices = user_actions
    form.action.default = 0
    form.net_ranges = net_ranges
    
    if request.method == 'POST' and form.validate():

        model = get_ipv6_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(webpicker_to_datetime(form.expires.data))
            flash_message = u'Existing IPv4 Rule found. Expiration time was updated to new value.'
        else:

            model = Flowspec6(
                source=form.source.data,
                source_mask=form.source_mask.data,
                source_port=form.source_port.data,
                destination=form.dest.data,
                destination_mask=form.dest_mask.data,
                destination_port=form.dest_port.data,
                next_header=form.next_header.data,
                flags=";".join(form.flags.data),
                packet_len=form.packet_len.data,
                expires=round_to_ten_minutes(webpicker_to_datetime(form.expires.data)),
                comment=quote_to_ent(form.comment.data),
                action_id=form.action.data,
                user_id=session['user_id'],
                rstate_id=get_state_by_time(webpicker_to_datetime(form.expires.data))
            )
            flash_message = u'IPv6 Rule saved'
            db.session.add(model)

        db.session.commit()
        flash(flash_message, 'alert-success')

        # announce routes
        if model.rstate_id == 1:
            route = messages.create_ipv6(model, constants.ANNOUNCE)
            announce_route(route)

        # log changes
        log_route(session['user_id'], model, RULE_TYPES['IPv6'], "{} / {}".format(session['user_email'], session['user_orgs']))

        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7)
    form.expires.data = datetime_to_webpicker(default_expires)

    return render_template('forms/ipv6_rule.j2', form=form, action_url=url_for('rules.ipv6_rule'))


@rules.route('/add_rtbh_rule', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def rtbh_rule():
    all_com = db.session.query(Community).all()
    if not all_com:
        insert_initial_communities()

    net_ranges = get_user_nets(session['user_id'])
    user_communities = get_user_communities(session['user_role_ids'])
    # setup form
    form = RTBHForm(request.form)
    user_communities =  [(0, '---- select community ----'),] + user_communities
    form.community.choices = user_communities
    form.net_ranges = net_ranges
    
    if request.method == 'POST' and form.validate():

        model = get_rtbh_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(webpicker_to_datetime(form.expires.data))
            flash_message = u'Existing RTBH Rule found. Expiration time was updated to new value.'
        else:

            model = RTBH(
                ipv4=form.ipv4.data,
                ipv4_mask=form.ipv4_mask.data,
                ipv6=form.ipv6.data,
                ipv6_mask=form.ipv6_mask.data,
                community_id=form.community.data,
                expires=round_to_ten_minutes(webpicker_to_datetime(form.expires.data)),
                comment=quote_to_ent(form.comment.data),
                user_id=session['user_id'],
                rstate_id=get_state_by_time(webpicker_to_datetime(form.expires.data))
            )
            db.session.add(model)
            db.session.commit()
            flash_message = u'RTBH Rule saved'

        flash(flash_message, 'alert-success')
        # announce routes
        if model.rstate_id == 1:
            route = messages.create_rtbh(model, constants.ANNOUNCE)
            announce_route(route)
        # log changes
        log_route(session['user_id'], model, RULE_TYPES['RTBH'],"{} / {}".format(session['user_email'], session['user_orgs']))

        return redirect(url_for('index'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    default_expires = datetime.now() + timedelta(days=7)
    form.expires.data = datetime_to_webpicker(default_expires)

    return render_template('forms/rtbh_rule.j2', form=form, action_url=url_for('rules.rtbh_rule'))


@rules.route('/export')
@auth_required
@admin_required
def export():
    rules4 = db.session.query(Flowspec4).order_by(Flowspec4.expires.desc()).all()
    rules6 = db.session.query(Flowspec6).order_by(Flowspec6.expires.desc()).all()
    rules = {4: rules4, 6: rules6}

    actions = db.session.query(Action).all()
    actions = {action.id: action for action in actions}

    rules_rtbh = db.session.query(RTBH).order_by(RTBH.expires.desc()).all()

    announce_all_routes()

    return render_template('pages/dashboard_admin.j2', rules=rules, actions=actions, rules_rtbh=rules_rtbh,
                           today=datetime.now())


@rules.route('/announce_all', methods=['GET'])
@localhost_only
def announce_all():
    announce_all_routes(constants.ANNOUNCE)
    return ' '


@rules.route('/withdraw_expired', methods=['GET'])
@localhost_only
def withdraw_expired():
    announce_all_routes(constants.WITHDRAW)
    return ' '


def announce_all_routes(action=constants.ANNOUNCE):
    """
    get routes from db and send it to ExaBGB api

    @TODO take the request away, use some kind of messaging (maybe celery?)
    :param action: action with routes - announce valid routes or withdraw expired routes
    """
    today = datetime.now()
    comp_func = ge if action == constants.ANNOUNCE else lt

    rules4 = db.session.query(Flowspec4).filter(Flowspec4.rstate_id == 1).filter(
        comp_func(Flowspec4.expires, today)).order_by(
        Flowspec4.expires.desc()).all()
    rules6 = db.session.query(Flowspec6).filter(Flowspec6.rstate_id == 1).filter(
        comp_func(Flowspec6.expires, today)).order_by(
        Flowspec6.expires.desc()).all()
    rules_rtbh = db.session.query(RTBH).filter(RTBH.rstate_id == 1).filter(comp_func(RTBH.expires, today)).order_by(
        RTBH.expires.desc()).all()

    output4 = [messages.create_ipv4(rule, action) for rule in rules4]
    output6 = [messages.create_ipv6(rule, action) for rule in rules6]
    output_rtbh = [messages.create_rtbh(rule, action) for rule in rules_rtbh]

    output = []
    output.extend(output4)
    output.extend(output6)
    output.extend(output_rtbh)

    for message in output:
        requests.post(app.config.get('EXA_API_URL'), data={'command': message})

    if action == constants.WITHDRAW:
        _a = [set_withdraw_state(rule) for rule in rules4]
        _a = [set_withdraw_state(rule) for rule in rules6]
        _a = [set_withdraw_state(rule) for rule in rules_rtbh]


def set_withdraw_state(rule):
    """
    set rule state to withdrawed in db
    :param rule: rule to update, can be any of rule types
    :return: none
    """
    rule.rstate_id = 2
    db.session.commit()
