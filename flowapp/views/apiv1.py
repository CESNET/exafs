from flask import Blueprint, request, jsonify
from functools import wraps
import jwt

from flowapp import app, db, validators, flowspec
from flowapp.models import Action, RTBH, Flowspec4, Flowspec6, Log, get_user_nets, get_user_actions
from flowapp.forms import RTBHForm, IPv4Form, IPv6Form


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
            data = jwt.decode(token,  app.config.get('JWT_SECRET'))
            current_user = data['user']
        except jwt.DecodeError:
            return jsonify({'message': 'auth token is invalid'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'auth token expired'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


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


@api.route('/rules/ipv4/', methods=['POST'])
@token_required
def ipv4_rule_create(current_user):
    net_ranges = get_user_nets(current_user['id'])
    form = IPv4Form(data=request.get_json())

    # add values to form instance
    # form.action.choices = get_user_actions(current_user['role_ids'])

    form.net_ranges = net_ranges

    if request.method == 'POST' and form.validate():

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
        return jsonify({'message': u'IPv4 Rule saved'}), 201

        # announce route
        # route = messages.create_ipv4(model, messages.ANNOUNCE)
        # announce_route(route)
        # log changes
        # log_route(model, RULE_TYPES['IPv4'])

        # return redirect(url_for('index'))
    else:
        valid_errors = []
        for field, errors in form.errors.items():
            for error in errors:
                valid_errors.append(u"Error in the {} field - {}".format(
                    getattr(form, field).label.text, error))

        #default_expires = datetime.now() + timedelta(days=7)
        #form.expires.data = datetime_to_webpicker(default_expires)

        return jsonify(valid_errors), 404


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