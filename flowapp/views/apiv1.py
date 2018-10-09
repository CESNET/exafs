import jwt

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta

from flowapp import app, db, validators, flowspec, csrf, messages
from flowapp.models import Action, RTBH, Flowspec4, Flowspec6, Log, get_user_nets, get_user_actions
from flowapp.forms import RTBHForm, IPv4Form, IPv6Form
from flowapp.utils import round_to_ten_minutes, webpicker_to_datetime
from flowapp.views.rules import announce_route, log_route, RULE_TYPES

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
    if user_key == app.config.get('API_KEY'):
        payload = {
            'user': {
                'uuid': 'jiri.vrany@tul.cz',
                'id': 1,
                'roles': ['admin'],
                'org': ['TU Liberec'],
                'role_ids': [2, 3],
                'org_ids': [1]
            },
            'exp': datetime.utcnow() + timedelta(minutes=30)
        }
        encoded = jwt.encode(payload, jwt_key, algorithm='HS256')
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
        print("PAYLOAD ADMIN", payload)
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
        print("PAYLOAD FILTERED", payload)
        return jsonify(payload)


@api.route('/rules/ipv4/', methods=['POST'])
@csrf.exempt
@token_required
def ipv4_rule_create(current_user):
    """
    Api method for new IPv4 rule
    :param current_user: data from jwt token
    :return: json response
    """
    net_ranges = get_user_nets(current_user['id'])
    form = IPv4Form(data=request.get_json())
    # add values to form instance
    form.action.choices = get_user_actions(current_user['role_ids'])
    form.net_ranges = net_ranges

    # if the form is not valid, we should return 404 with errors
    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 404

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
        expires=round_to_ten_minutes(webpicker_to_datetime(form.expires.data)),
        comment=form.comment.data,
        action_id=form.action.data,
        user_id=current_user['id'],
        rstate_id=1
    )

    db.session.add(model)
    db.session.commit()

    # announce route
    route = messages.create_ipv4(model, messages.ANNOUNCE)
    # @TODO - refactor move announce route out of rules view
    announce_route(route)
    # log changes
    # @TODO - log routes from api
    # log_route(model, RULE_TYPES['IPv4'])

    return jsonify({'message': u'IPv4 Rule saved', 'rule': model.to_dict()}), 201


@api.route('/rules/ipv6/', methods=['POST'])
@token_required
def ipv6_rule(current_user):
    """
    Create new IPv6 rule
    :param current_user: data from jwt token
    :return:
    """
    net_ranges = get_user_nets(current_user['id'])
    form = IPv6Form(data=request.get_json())
    form.action.choices = get_user_actions(current_user['role_ids'])
    form.net_ranges = net_ranges

    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 404

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
        comment=form.comment.data,
        action_id=form.action.data,
        user_id=current_user['id'],
        rstate_id=1
    )
    db.session.add(model)
    db.session.commit()

    # announce routes
    route = messages.create_ipv6(model, messages.ANNOUNCE)
    announce_route(route)

    # log changes
    #log_route(model, RULE_TYPES['IPv6'])

    return jsonify({'message': u'IPv6 Rule saved', 'rule': model.to_dict()}), 201



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
    if model:
        if model.user_id == current_user['id']:
            return jsonify(model.to_dict()), 200
        else:
            return jsonify({'message': 'not allowed to view this rule'}), 401
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
    errors = form.errors.items()
    if len(errors) > 1:
        for field, field_errors in form.errors.items():
            for field_error in field_errors:
                valid_errors.append(u"Error in the {} - {}".format(
                    getattr(form, field).label.text, field_error))

        return {'message': 'error - invalid request data','validation_errors': valid_errors}

    # if the only error is in CSRF then it is ok - csrf is exempt for this view
    elif len(errors) == 1 and errors[0][0] != 'csrf_token':
        return {'message': 'error - invalid request data','validation_errors': errors[0][0]}
    else:
        return False