import jwt
import ipaddress

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta

import flowapp.constants
from flowapp import app, db, validators, flowspec, csrf, messages
from flowapp.models import RTBH, Flowspec4, Flowspec6, ApiKey, Community, get_user_nets, get_user_actions, \
    get_ipv4_model_if_exists, get_ipv6_model_if_exists, insert_initial_communities, get_user_communities, \
    get_rtbh_model_if_exists
from flowapp.forms import IPv4Form, IPv6Form, RTBHForm
from flowapp.utils import round_to_ten_minutes, webpicker_to_datetime, quote_to_ent, get_state_by_time, \
     parse_api_time, output_date_format
from flowapp.auth import check_access_rights
from flowapp.output import ROUTE_MODELS, RULE_TYPES, announce_route, log_route, log_withdraw

api = Blueprint('apiv1', __name__, template_folder='templates')


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'auth token is missing'}), 401

        try:
            data = jwt.decode(token, app.config.get('JWT_SECRET'), algorithms=['HS256'])
            current_user = data['user']
        except jwt.DecodeError:
            return jsonify({'message': 'auth token is invalid'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'auth token expired'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@api.route('/auth/<string:user_key>', methods=['GET'])
def authorize(user_key):
    """
    Generate API Key for the loged user using PyJWT
    :return: page with token
    """
    jwt_key = app.config.get('JWT_SECRET')

    model = db.session.query(ApiKey).filter_by(key=user_key).first()

    if model and ipaddress.ip_address(model.machine) == ipaddress.ip_address(
            request.remote_addr):
        payload = {
            'user': {
                'uuid': model.user.uuid,
                'id': model.user.id,
                'roles': [role.name for role in model.user.role.all()],
                'org': [org.name for org in model.user.organization.all()],
                'role_ids': [role.id for role in model.user.role.all()],
                'org_ids': [org.id for org in model.user.organization.all()]
            },
            'exp': datetime.now() + timedelta(minutes=30)
        }
        encoded = jwt.encode(payload, jwt_key, algorithm='HS256').decode("utf-8")

        return jsonify({'token': encoded})
    else:
        return jsonify({'message': 'auth token is invalid'}), 403


@api.route('/rules')
@token_required
def index(current_user):
    net_ranges = get_user_nets(current_user['id'])

    rules4 = db.session.query(Flowspec4).order_by(Flowspec4.expires.desc()).all()
    rules6 = db.session.query(Flowspec6).order_by(Flowspec6.expires.desc()).all()
    rules_rtbh = db.session.query(RTBH).order_by(RTBH.expires.desc()).all()

    # admin can see and edit any rules
    if 3 in current_user['role_ids']:
        payload = {
            "ipv4_rules": [rule.to_dict() for rule in rules4],
            "ipv6_rules": [rule.to_dict() for rule in rules6],
            "rules_rtbh": [rule.to_dict() for rule in rules_rtbh]
        }
        return jsonify(payload)
    # filter out the rules for normal users
    else:
        rules4 = validators.filter_rules_in_network(net_ranges, rules4)
        rules6 = validators.filter_rules_in_network(net_ranges, rules6)
        rules_rtbh = validators.filter_rtbh_rules(net_ranges, rules_rtbh)

        user_actions = get_user_actions(current_user['role_ids'])
        user_actions = [act[0] for act in user_actions]

        rules4_editable, rules4_visible = flowspec.filter_rules_action(user_actions, rules4)
        rules6_editable, rules6_visible = flowspec.filter_rules_action(user_actions, rules6)

        payload = {
            "ipv4_rules": [rule.to_dict() for rule in rules4_editable],
            "ipv6_rules": [rule.to_dict() for rule in rules6_editable],
            "ipv4_rules_readonly": [rule.to_dict() for rule in rules4_visible],
            "ipv6_rules_readonly": [rule.to_dict() for rule in rules6_visible],
            "rtbh_rules": [rule.to_dict() for rule in rules_rtbh]
        }
        return jsonify(payload)


@api.route('/actions')
@token_required
def all_actions(current_user):
    """
    Returns Actions allowed for current user
    :param current_user:
    :return: json response
    """

    actions = get_user_actions(current_user['role_ids'])
    if actions:
        return jsonify(actions)
    else:
        return jsonify({'message': 'no actions for this user?'}), 404


@api.route('/communities')
@token_required
def all_communities(current_user):
    """
    Returns RTHB communites allowed for current user
    :param current_user:
    :return: json response
    """

    coms = get_user_communities(current_user['role_ids'])
    if coms:
        return jsonify(coms)
    else:
        return jsonify({'message': 'no actions for this user?'}), 404


@api.route('/rules/ipv4', methods=['POST'])
@csrf.exempt
@token_required
def create_ipv4(current_user):
    """
    Api method for new IPv4 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return: json response
    """
    net_ranges = get_user_nets(current_user['id'])
    json_request_data = request.get_json()
    form = IPv4Form(data=json_request_data)
    # add values to form instance
    form.action.choices = get_user_actions(current_user['role_ids'])
    form.net_ranges = net_ranges

    # if the form is not valid, we should return 404 with errors
    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    model = get_ipv4_model_if_exists(form.data, 1)

    if model:
        model.expires, pref_format = parse_api_time(form.expires.data)
        flash_message = u'Existing IPv4 Rule found. Expiration time was updated to new value.'
    else:
        expires, pref_format = parse_api_time(form.expires.data)
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
            expires=expires,
            comment=quote_to_ent(form.comment.data),
            action_id=form.action.data,
            user_id=current_user['id'],
            rstate_id=get_state_by_time(expires)
        )
        flash_message = u'IPv4 Rule saved'
        db.session.add(model)

    db.session.commit()

    # announce route if model is in active state
    if model.rstate_id == 1:
        route = messages.create_ipv4(model, flowapp.constants.ANNOUNCE)
        announce_route(route)

    # log changes
    log_route(current_user['id'], model, RULE_TYPES['IPv4'])

    pref_format = output_date_format(json_request_data, pref_format)
    return jsonify({'message': flash_message, 'rule': model.to_dict(pref_format)}), 201


@api.route('/rules/ipv6', methods=['POST'])
@csrf.exempt
@token_required
def create_ipv6(current_user):
    """
    Create new IPv6 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return:
    """
    net_ranges = get_user_nets(current_user['id'])
    json_request_data = request.get_json()
    form = IPv6Form(data=json_request_data)
    form.action.choices = get_user_actions(current_user['role_ids'])
    form.net_ranges = net_ranges

    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    model = get_ipv6_model_if_exists(form.data, 1)

    if model:
        model.expires, pref_format = parse_api_time(form.expires.data)
        flash_message = u'Existing IPv6 Rule found. Expiration time was updated to new value.'
    else:
        expires, pref_format = parse_api_time(form.expires.data)
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
            expires=expires,
            comment=quote_to_ent(form.comment.data),
            action_id=form.action.data,
            user_id=current_user['id'],
            rstate_id=get_state_by_time(expires)
        )
        flash_message = u'IPv6 Rule saved'
        db.session.add(model)

    db.session.commit()

    # announce routes
    if model.rstate_id == 1:
        route = messages.create_ipv6(model, flowapp.constants.ANNOUNCE)
        announce_route(route)

    # log changes
    log_route(current_user['id'], model, RULE_TYPES['IPv6'])

    pref_format = output_date_format(json_request_data, pref_format)
    return jsonify({'message': flash_message, 'rule': model.to_dict(pref_format)}), 201


@api.route('/rules/rtbh', methods=['POST'])
@csrf.exempt
@token_required
def create_rtbh(current_user):
    all_com = db.session.query(Community).all()
    if not all_com:
        insert_initial_communities()

    net_ranges = get_user_nets(current_user['id'])

    json_request_data = request.get_json()
    form = RTBHForm(data=json_request_data)

    form.community.choices = get_user_communities(current_user['role_ids'])
    form.net_ranges = net_ranges

    if 3 not in current_user['role_ids']:
        if form.ipv4.data:
            form.ipv4_mask.data = 32

        if form.ipv6.data:
            form.ipv6_mask.data = 128

    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    model = get_rtbh_model_if_exists(form.data, 1)

    if model:
        model.expires, pref_format = parse_api_time(form.expires.data)
        flash_message = u'Existing RTBH Rule found. Expiration time was updated to new value.'
    else:
        expires, pref_format = parse_api_time(form.expires.data)
        model = RTBH(
            ipv4=form.ipv4.data,
            ipv4_mask=form.ipv4_mask.data,
            ipv6=form.ipv6.data,
            ipv6_mask=form.ipv6_mask.data,
            community_id=form.community.data,
            expires=expires,
            comment=quote_to_ent(form.comment.data),
            user_id=current_user['id'],
            rstate_id=get_state_by_time(expires)
        )
        db.session.add(model)
        db.session.commit()
        flash_message = u'RTBH Rule saved'

    # announce routes
    if model.rstate_id == 1:
        route = messages.create_rtbh(model, flowapp.constants.ANNOUNCE)
        announce_route(route)
    # log changes
    log_route(current_user['id'], model, RULE_TYPES['RTBH'])

    pref_format = output_date_format(json_request_data, pref_format)
    return jsonify({'message': flash_message, 'rule': model.to_dict(pref_format)}), 201


@api.route('/rules/ipv4/<int:rule_id>', methods=['GET'])
@token_required
def ipv4_rule_get(current_user, rule_id):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    model = db.session.query(Flowspec4).get(rule_id)
    return get_rule(current_user, model, rule_id)


@api.route('/rules/ipv6/<int:rule_id>', methods=['GET'])
@token_required
def ipv6_rule_get(current_user, rule_id):
    """
    Return IPv6 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    model = db.session.query(Flowspec6).get(rule_id)
    return get_rule(current_user, model, rule_id)


@api.route('/rules/rtbh/<int:rule_id>', methods=['GET'])
@token_required
def rtbh_rule_get(current_user, rule_id):
    """
    Return RTBH rule
    :param current_user:
    :param rule_id:
    :return:
    """
    model = db.session.query(RTBH).get(rule_id)
    return get_rule(current_user, model, rule_id)


def get_rule(current_user, model, rule_id):
    """
    Common rule getter - return ipv4 or ipv6 model data
    :param model: rule model
    :return: json
    """
    if model:
        if check_access_rights(current_user, model.user_id):
            return jsonify(model.to_dict()), 200
        else:
            return jsonify({'message': 'not allowed to view this rule'}), 401
    else:
        return jsonify({'message': 'rule {} not found '.format(rule_id)}), 404


@api.route('/rules/ipv4/<int:rule_id>', methods=['DELETE'])
@token_required
def delete_v4_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = Flowspec4
    route_model = messages.create_ipv4
    return delete_rule(current_user, rule_id, model_name, route_model, 4)


@api.route('/rules/ipv6/<int:rule_id>', methods=['DELETE'])
@token_required
def delete_v6_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = Flowspec6
    route_model = messages.create_ipv6
    return delete_rule(current_user, rule_id, model_name, route_model, 6)


@api.route('/rules/rtbh/<int:rule_id>', methods=['DELETE'])
@token_required
def delete_rtbh_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = RTBH
    route_model = messages.create_rtbh
    return delete_rule(current_user, rule_id, model_name, route_model, 1)


def delete_rule(current_user, rule_id, model_name, route_model, rule_type):
    """
    Common method for deleting ipv4 or ipv6 rules
    :param current_user:
    :param rule_id:
    :param model_name:
    :param route_model:
    :return:
    """
    model = db.session.query(model_name).get(rule_id)
    if model:
        if check_access_rights(current_user, model.user_id):
            # withdraw route
            route = route_model(model, flowapp.constants.WITHDRAW)
            announce_route(route)

            log_withdraw(current_user['id'], route, rule_type, model.id)
            # delete from db
            db.session.delete(model)
            db.session.commit()
            return jsonify({'message': 'rule deleted'}), 201
        else:
            return jsonify({'message': 'not allowed to delete this rule'}), 401
    else:
        return jsonify({'message': 'rule {} not found '.format(rule_id)}), 404


@api.route('/test_token', methods=['GET'])
@token_required
def token_test_get(current_user):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    return jsonify({'message': 'token works as expected', 'uuid': current_user['uuid']}), 200


def get_form_errors(form):
    valid_errors = []

    # if the only error is in CSRF then it is ok - csrf is exempt for this view
    del (form.errors['csrf_token'])

    errors = form.errors.items()
    if len(errors) > 0:
        return {'message': 'error - invalid request data', 'validation_errors': form.errors}

    return False


