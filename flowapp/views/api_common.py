import jwt
import ipaddress

from flask import request, jsonify, current_app
from functools import wraps
from datetime import datetime, timedelta

from flowapp.constants import RULE_NAMES_DICT, WITHDRAW, TIME_FORMAT_ARG, RuleTypes
from flowapp.models import (
    RTBH,
    Flowspec4,
    Flowspec6,
    ApiKey,
    MachineApiKey,
    Community,
    Organization,
    check_global_rule_limit,
    check_rule_limit,
    get_user_nets,
    get_user_actions,
    insert_initial_communities,
    get_user_communities,
)
from flowapp.forms import IPv4Form, IPv6Form, RTBHForm
from flowapp.services import rule_service
from flowapp.utils import (
    output_date_format,
)
from flowapp.auth import check_access_rights
from flowapp.output import announce_route, log_withdraw, Route, RouteSources


from flowapp import db, validators, flowspec, messages


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]

        if not token:
            return jsonify({"message": "auth token is missing"}), 401

        try:
            data = jwt.decode(token, current_app.config.get("JWT_SECRET"), algorithms=["HS256"])
            current_user = data["user"]
        except jwt.DecodeError:
            return jsonify({"message": "auth token is invalid"}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "auth token expired"}), 401

        return f(current_user=current_user, *args, **kwargs)

    return decorated


def authorize(user_key):
    """
    Generate API Key for the loged user using PyJWT
    :return: page with token
    """
    jwt_key = current_app.config.get("JWT_SECRET")
    # try normal user key first
    model = db.session.query(ApiKey).filter_by(key=user_key).first()
    # if not found try machine key
    if not model:
        model = db.session.query(MachineApiKey).filter_by(key=user_key).first()
    # if key is not found return 403
    if not model:
        return jsonify({"message": "auth token is invalid"}), 403

    # check if the key is not expired
    if model.is_expired():
        return jsonify({"message": "auth token is expired"}), 401

    # check if the key is not used by different machine
    if model and ipaddress.ip_address(model.machine) == ipaddress.ip_address(request.remote_addr):
        payload = {
            "user": {
                "uuid": model.user.uuid,
                "id": model.user.id,
                "readonly": model.readonly,
                "roles": [role.name for role in model.user.role.all()],
                "org": model.org.name,
                "org_id": model.org.id,
                "role_ids": [role.id for role in model.user.role.all()],
            },
            "exp": datetime.now() + timedelta(minutes=30),
        }
        # encoded = jwt.encode(payload, jwt_key, algorithm="HS256").decode("utf-8")
        encoded = jwt.encode(payload, jwt_key, algorithm="HS256")

        return jsonify({"token": encoded})
    else:
        return jsonify({"message": f"auth token is not valid from machine {request.remote_addr}"}), 403


def check_readonly(func):
    """
    Check if the token is readonly
    Used in api endpoints
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        # Access read only flag from first of the args
        current_user = kwargs.get("current_user", False)
        read_only = current_user.get("readonly", False)
        if read_only:
            return jsonify({"message": "read only token can't perform this action"}), 403
        return func(*args, **kwargs)

    return decorated_function


# endpints


def index(current_user, key_map):
    prefered_tf = request.args.get(TIME_FORMAT_ARG) if request.args.get(TIME_FORMAT_ARG) else ""

    net_ranges = get_user_nets(current_user["id"])
    rules4 = db.session.query(Flowspec4).order_by(Flowspec4.expires.desc()).all()
    rules6 = db.session.query(Flowspec6).order_by(Flowspec6.expires.desc()).all()
    rules_rtbh = db.session.query(RTBH).order_by(RTBH.expires.desc()).all()

    # admin can see and edit any rules
    if 3 in current_user["role_ids"]:
        payload = {
            key_map["ipv4_rules"]: [rule.to_dict(prefered_tf) for rule in rules4],
            key_map["ipv6_rules"]: [rule.to_dict(prefered_tf) for rule in rules6],
            key_map["rtbh_rules"]: [rule.to_dict(prefered_tf) for rule in rules_rtbh],
        }
        return jsonify(payload)
    # filter out the rules for normal users
    else:
        rules4 = validators.filter_rules_in_network(net_ranges, rules4)
        rules6 = validators.filter_rules_in_network(net_ranges, rules6)
        rules_rtbh = validators.filter_rtbh_rules(net_ranges, rules_rtbh)

        user_actions = get_user_actions(current_user["role_ids"])
        user_actions = [act[0] for act in user_actions]

        rules4_editable, rules4_visible = flowspec.filter_rules_action(user_actions, rules4)
        rules6_editable, rules6_visible = flowspec.filter_rules_action(user_actions, rules6)

        payload = {
            key_map["ipv4_rules"]: [rule.to_dict(prefered_tf) for rule in rules4_editable],
            key_map["ipv6_rules"]: [rule.to_dict(prefered_tf) for rule in rules6_editable],
            key_map["ipv4_rules_readonly"]: [rule.to_dict(prefered_tf) for rule in rules4_visible],
            key_map["ipv6_rules_readonly"]: [rule.to_dict(prefered_tf) for rule in rules6_visible],
            key_map["rtbh_rules"]: [rule.to_dict(prefered_tf) for rule in rules_rtbh],
        }
        return jsonify(payload)


def all_actions(current_user):
    """
    Returns Actions allowed for current user
    :param current_user:
    :return: json response
    """

    actions = get_user_actions(current_user["role_ids"])
    if actions:
        return jsonify(actions)
    else:
        return jsonify({"message": "no actions for this user?"}), 404


def all_communities(current_user):
    """
    Returns RTHB communites allowed for current user
    :param current_user:
    :return: json response
    """

    coms = get_user_communities(current_user["role_ids"])
    if coms:
        return jsonify(coms)
    else:
        return jsonify({"message": "no actions for this user?"}), 404


def limit_reached(count, rule_type, org_id):
    rule_name = RULE_NAMES_DICT[rule_type.value]
    org = db.session.get(Organization, org_id)
    if rule_type == RuleTypes.IPv4:
        limit = org.limit_flowspec4
    elif rule_type == RuleTypes.IPv6:
        limit = org.limit_flowspec6
    elif rule_type == RuleTypes.RTBH:
        limit = org.rtbh

    return (
        jsonify({"message": f"Rule limit {limit} reached for {rule_name}, currently you have {count} active rules."}),
        403,
    )


def global_limit_reached(count, rule_type):
    rule_name = RULE_NAMES_DICT[rule_type.value]
    if rule_type == RuleTypes.IPv4 or rule_type == RuleTypes.IPv6:
        limit = current_app.config.get("FLOWSPEC_MAX_RULES")
    elif rule_type == RuleTypes.RTBH:
        limit = current_app.config.get("RTBH_MAX_RULES")

    return (
        jsonify(
            {"message": f"System limit {limit} reached for {rule_name}. Currently there are {count} active rules."}
        ),
        403,
    )


def create_ipv4(current_user):
    """
    Api method for new IPv4 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return: json response
    """
    if check_global_rule_limit(RuleTypes.IPv4):
        count = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
        return global_limit_reached(count=count, rule_type=RuleTypes.IPv4)

    if check_rule_limit(current_user["org_id"], RuleTypes.IPv4):
        count = db.session.query(Flowspec4).filter_by(rstate_id=1, org_id=current_user["org_id"]).count()
        return limit_reached(count=count, rule_type=RuleTypes.IPv4, org_id=current_user["org_id"])

    net_ranges = get_user_nets(current_user["id"])
    json_request_data = request.get_json()
    form = IPv4Form(data=json_request_data, meta={"csrf": False})
    # add values to form instance
    form.action.choices = get_user_actions(current_user["role_ids"])
    form.net_ranges = net_ranges

    # if the form is not valid, we should return 404 with errors
    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    # Use the service to create/update the rule
    model, flash_message = rule_service.create_or_update_ipv4_rule(
        form_data=form.data,
        user_id=current_user["id"],
        org_id=current_user["org_id"],
        user_email=current_user["uuid"],
        org_name=current_user["org"],
    )

    pref_format = output_date_format(json_request_data, form.expires.pref_format)
    response = {"message": flash_message, "rule": model.to_dict(pref_format)}
    return jsonify(response), 201


def create_ipv6(current_user):
    """
    Create new IPv6 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return:
    """
    if check_global_rule_limit(RuleTypes.IPv6):
        count = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
        return global_limit_reached(count=count, rule_type=RuleTypes.IPv6)

    if check_rule_limit(current_user["org_id"], RuleTypes.IPv6):
        count = db.session.query(Flowspec6).filter_by(rstate_id=1, org_id=current_user["org_id"]).count()
        return limit_reached(count=count, rule_type=RuleTypes.IPv6, org_id=current_user["org_id"])

    net_ranges = get_user_nets(current_user["id"])
    json_request_data = request.get_json()
    form = IPv6Form(data=json_request_data, meta={"csrf": False})
    form.action.choices = get_user_actions(current_user["role_ids"])
    form.net_ranges = net_ranges

    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    model, flash_message = rule_service.create_or_update_ipv6_rule(
        form_data=form.data,
        user_id=current_user["id"],
        org_id=current_user["org_id"],
        user_email=current_user["uuid"],
        org_name=current_user["org"],
    )

    pref_format = output_date_format(json_request_data, form.expires.pref_format)
    return jsonify({"message": flash_message, "rule": model.to_dict(pref_format)}), 201


def create_rtbh(current_user):
    """
    Create new RTBH rule
    """
    if check_global_rule_limit(RuleTypes.RTBH):
        count = db.session.query(RTBH).filter_by(rstate_id=1).count()
        return global_limit_reached(count=count, rule_type=RuleTypes.RTBH)

    if check_rule_limit(current_user["org_id"], RuleTypes.RTBH):
        count = db.session.query(RTBH).filter_by(rstate_id=1, org_id=current_user["org_id"]).count()
        return limit_reached(count=count, rule_type=RuleTypes.RTBH, org_id=current_user["org_id"])

    all_com = db.session.query(Community).all()
    if not all_com:
        insert_initial_communities()

    net_ranges = get_user_nets(current_user["id"])

    json_request_data = request.get_json()
    form = RTBHForm(data=json_request_data, meta={"csrf": False})

    form.community.choices = get_user_communities(current_user["role_ids"])
    form.net_ranges = net_ranges

    if not form.validate():
        form_errors = get_form_errors(form)
        if form_errors:
            return jsonify(form_errors), 400

    model, flash_message = rule_service.create_or_update_rtbh_rule(
        form_data=form.data,
        user_id=current_user["id"],
        org_id=current_user["org_id"],
        user_email=current_user["uuid"],
        org_name=current_user["org"],
    )

    pref_format = output_date_format(json_request_data, form.expires.pref_format)
    return jsonify({"message": flash_message, "rule": model.to_dict(pref_format)}), 201


def ipv4_rule_get(current_user, rule_id):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    model = db.session.get(Flowspec4, rule_id)
    return get_rule(current_user, model, rule_id)


def ipv6_rule_get(current_user, rule_id):
    """
    Return IPv6 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    model = db.session.get(Flowspec6, rule_id)
    return get_rule(current_user, model, rule_id)


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
    prefered_tf = request.args.get(TIME_FORMAT_ARG) if request.args.get(TIME_FORMAT_ARG) else ""

    if model:
        if check_access_rights(current_user, model.user_id):
            return jsonify(model.to_dict(prefered_tf)), 200
        else:
            return jsonify({"message": "not allowed to view this rule"}), 401
    else:
        return jsonify({"message": "rule {} not found ".format(rule_id)}), 404


def delete_v4_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = Flowspec4
    route_model = messages.create_ipv4
    return delete_rule(current_user, rule_id, model_name, route_model, RuleTypes.IPv4)


def delete_v6_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = Flowspec6
    route_model = messages.create_ipv6
    return delete_rule(current_user, rule_id, model_name, route_model, RuleTypes.IPv6)


def delete_rtbh_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    model_name = RTBH
    route_model = messages.create_rtbh
    return delete_rule(current_user, rule_id, model_name, route_model, RuleTypes.RTBH)


def delete_rule(current_user, rule_id, model_name, route_model, rule_type):
    """
    Common method for deleting ipv4 or ipv6 rules
    :param current_user:
    :param rule_id:
    :param model_name:
    :param route_model:
    :return:
    """
    model = db.session.get(model_name, rule_id)
    if model:
        if check_access_rights(current_user, model.user_id):
            # withdraw route
            command = route_model(model, WITHDRAW)
            route = Route(
                author=f"{current_user['uuid']} / {current_user['org']}",
                source=RouteSources.API,
                command=command,
            )
            announce_route(route)

            log_withdraw(
                current_user["id"],
                route.command,
                rule_type,
                model.id,
                f"{current_user['uuid']} / {current_user['org']}",
            )
            # delete from db
            db.session.delete(model)
            db.session.commit()
            return jsonify({"message": "rule deleted"}), 201
        else:
            return jsonify({"message": "not allowed to delete this rule"}), 401
    else:
        return jsonify({"message": "rule {} not found ".format(rule_id)}), 404


def token_test_get(current_user):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    my_response = {
        "message": "token works as expected",
        "uuid": current_user["uuid"],
        "readonly": current_user["readonly"],
    }
    return jsonify(my_response), 200


def get_form_errors(form):
    # if the only error is in CSRF then it is ok - csrf is exempt for this view
    try:
        del form.errors["csrf_token"]
    except KeyError:
        pass

    errors = form.errors.items()
    if len(errors) > 0:
        return {
            "message": "error - invalid request data",
            "validation_errors": form.errors,
        }

    return False
