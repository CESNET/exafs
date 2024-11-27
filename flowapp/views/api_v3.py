from flask import Blueprint, request
from flowapp import csrf
from flowapp.views import api_common

api = Blueprint("api_v3", __name__, template_folder="templates")


@api.route("/auth", methods=["GET"])
def authorize():
    mkey = request.headers.get("x-api-key", None)
    return api_common.authorize(mkey)


@api.route("/rules")
@api_common.token_required
def index(current_user):
    key_map = {
        "ipv4_rules": "flowspec_ipv4_rw",
        "ipv6_rules": "flowspec_ipv6_rw",
        "rtbh_rules": "rtbh_any_rw",
        "ipv4_rules_readonly": "flowspec_ipv4_ro",
        "ipv6_rules_readonly": "flowspec_ipv6_ro",
        "rtbh_rules_readonly": "rtbh_any_ro",
    }
    return api_common.index(current_user, key_map)


@api.route("/actions")
@api_common.token_required
def all_actions(current_user):
    """
    Returns Actions allowed for current user
    :param current_user:
    :return: json response
    """
    return api_common.all_actions(current_user)


@api.route("/communities")
@api_common.token_required
def all_communities(current_user):
    """
    Returns RTHB communites allowed for current user
    :param current_user:
    :return: json response
    """
    return api_common.all_communities(current_user)


@api.route("/rules/ipv4", methods=["POST"])
@api_common.token_required
@api_common.check_readonly
def create_ipv4(current_user):
    """
    Api method for new IPv4 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return: json response
    """
    return api_common.create_ipv4(current_user)


@api.route("/rules/ipv6", methods=["POST"])
@csrf.exempt
@api_common.token_required
@api_common.check_readonly
def create_ipv6(current_user):
    """
    Create new IPv6 rule
    :param data: parsed json request
    :param current_user: data from jwt token
    :return:
    """
    return api_common.create_ipv6(current_user)


@api.route("/rules/rtbh", methods=["POST"])
@csrf.exempt
@api_common.token_required
@api_common.check_readonly
def create_rtbh(current_user):
    return api_common.create_rtbh(current_user)


@api.route("/rules/ipv4/<int:rule_id>", methods=["GET"])
@api_common.token_required
def ipv4_rule_get(current_user, rule_id):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    return api_common.ipv4_rule_get(current_user, rule_id)


@api.route("/rules/ipv6/<int:rule_id>", methods=["GET"])
@api_common.token_required
def ipv6_rule_get(current_user, rule_id):
    """
    Return IPv6 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    return api_common.ipv6_rule_get(current_user, rule_id)


@api.route("/rules/rtbh/<int:rule_id>", methods=["GET"])
@api_common.token_required
def rtbh_rule_get(current_user, rule_id):
    """
    Return RTBH rule
    :param current_user:
    :param rule_id:
    :return:
    """
    return api_common.rtbh_rule_get(current_user, rule_id)


@api.route("/rules/ipv4/<int:rule_id>", methods=["DELETE"])
@api_common.token_required
@api_common.check_readonly
def delete_v4_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    return api_common.delete_v4_rule(current_user, rule_id)


@api.route("/rules/ipv6/<int:rule_id>", methods=["DELETE"])
@api_common.token_required
@api_common.check_readonly
def delete_v6_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    return api_common.delete_v6_rule(current_user, rule_id)


@api.route("/rules/rtbh/<int:rule_id>", methods=["DELETE"])
@api_common.token_required
@api_common.check_readonly
def delete_rtbh_rule(current_user, rule_id):
    """
    Delete rule with given id and type
    :param rule_id: integer - rule id
    """
    return api_common.delete_rtbh_rule(current_user, rule_id)


@api.route("/test_token", methods=["GET"])
@api_common.token_required
def token_test_get(current_user):
    """
    Return IPv4 rule
    :param current_user:
    :param rule_id:
    :return:
    """
    return api_common.token_test_get(current_user)
