# flowapp/views/admin.py
from datetime import datetime, timedelta
from collections import namedtuple

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from flowapp import constants, db
from flowapp.auth import (
    admin_required,
    auth_required,
    is_admin,
    localhost_only,
    user_or_admin_required,
)
from flowapp.constants import RuleTypes
from flowapp.forms import IPv4Form, IPv6Form, RTBHForm
from flowapp.models import (
    RTBH,
    Action,
    Community,
    Flowspec4,
    Flowspec6,
    Organization,
    check_global_rule_limit,
    check_rule_limit,
    get_user_actions,
    get_user_communities,
    get_user_nets,
    insert_initial_communities,
)
from flowapp.models.log import Log
from flowapp.output import ROUTE_MODELS, announce_route, log_route, log_withdraw, RouteSources, Route
from flowapp.services import rule_service, announce_all_routes, delete_expired_whitelists
from flowapp.utils import (
    flash_errors,
    get_state_by_time,
    round_to_ten_minutes,
)
from flowapp.auth import get_user_allowed_rule_ids, check_user_can_modify_rule


rules = Blueprint("rules", __name__, template_folder="templates")

DATA_MODELS = {1: RTBH, 4: Flowspec4, 6: Flowspec6}
DATA_MODELS_NAMED = {"rtbh": RTBH, "ipv4": Flowspec4, "ipv6": Flowspec6}
DATA_FORMS = {1: RTBHForm, 4: IPv4Form, 6: IPv6Form}
DATA_FORMS_NAMED = {"rtbh": RTBHForm, "ipv4": IPv4Form, "ipv6": IPv6Form}
DATA_TEMPLATES = {
    1: "forms/rtbh_rule.html",
    4: "forms/ipv4_rule.html",
    6: "forms/ipv6_rule.html",
}
DATA_TABLES = {1: "RTBH", 4: "flowspec4", 6: "flowspec6"}
DEFAULT_SORT = {1: "ivp4", 4: "source", 6: "source"}


@rules.route("/reactivate/<int:rule_type>/<int:rule_id>", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def reactivate_rule(rule_type, rule_id):
    """
    Set new time for the rule of given type identified by id
    :param rule_type: integer - type of rule, corresponds to RuleTypes enum value
    :param rule_id: integer - id of the rule
    """
    # Convert the integer rule_type to RuleTypes enum
    enum_rule_type = RuleTypes(rule_type)

    # Now use the enum value where needed but the integer for dictionary lookups
    model_name = DATA_MODELS[rule_type]
    form_name = DATA_FORMS[rule_type]

    model = db.session.get(model_name, rule_id)
    if not model:
        flash("Rule not found", "alert-danger")
        return redirect(url_for("index"))

    form = form_name(request.form, obj=model)
    form.net_ranges = get_user_nets(session["user_id"])

    if rule_type > 2:
        form.action.choices = [(g.id, g.name) for g in db.session.query(Action).order_by("name")]
        form.action.data = model.action_id

    if rule_type == RuleTypes.RTBH.value:
        form.community.choices = get_user_communities(session["user_role_ids"])
        form.community.data = model.community_id

    if rule_type == RuleTypes.IPv4.value:
        form.protocol.data = model.protocol

    if rule_type == RuleTypes.IPv6.value:
        form.next_header.data = model.next_header

    # Process form submission
    if request.method == "POST":
        # Round expiration time to 10 minutes
        expires = round_to_ten_minutes(form.expires.data)

        # Use the service to reactivate the rule
        _, messages = rule_service.reactivate_rule(
            rule_type=enum_rule_type,
            rule_id=rule_id,
            expires=expires,
            comment=form.comment.data,
            user_id=session["user_id"],
            org_id=session["user_org_id"],
            user_email=session["user_email"],
            org_name=session["user_org"],
        )

        # Handle special messages (redirects)
        if "global_limit_reached" in messages:
            return redirect(url_for("rules.global_limit_reached", rule_type=rule_type))
        if "limit_reached" in messages:
            return redirect(url_for("rules.limit_reached", rule_type=rule_type))

        for message in messages:
            flash(message, "alert-success")

        return redirect(
            url_for(
                "dashboard.index",
                rtype=session[constants.TYPE_ARG],
                rstate=session[constants.RULE_ARG],
                sort=session[constants.SORT_ARG],
                squery=session[constants.SEARCH_ARG],
                order=session[constants.ORDER_ARG],
            )
        )
    else:
        flash_errors(form)

    # For GET requests, prepare the form for display
    form.expires.data = model.expires
    for field in form:
        if field.name not in ["expires", "csrf_token", "comment"]:
            field.render_kw = {"disabled": "disabled"}

    action_url = url_for("rules.reactivate_rule", rule_type=rule_type, rule_id=rule_id)

    return render_template(
        DATA_TEMPLATES[rule_type],
        form=form,
        action_url=action_url,
        editing=True,
        title="Update",
    )


@rules.route("/delete/<int:rule_type>/<int:rule_id>", methods=["GET"])
@auth_required
@user_or_admin_required
def delete_rule(rule_type, rule_id):
    """
    Delete rule with given id and type
    :param rule_type: integer - type of rule to be deleted
    :param rule_id: integer - rule id
    """
    # Convert the integer rule_type to RuleTypes enum
    enum_rule_type = RuleTypes(rule_type)

    # Get the rule type string for access checking
    rule_type_map = {RuleTypes.IPv4.value: "ipv4", RuleTypes.IPv6.value: "ipv6", RuleTypes.RTBH.value: "rtbh"}
    rule_type_str = rule_type_map.get(rule_type)

    # Check if user can modify this rule
    if not check_user_can_modify_rule(rule_id, rule_type_str):
        flash("You cannot delete this rule", "alert-warning")
        return redirect(
            url_for(
                "dashboard.index",
                rtype=session[constants.TYPE_ARG],
                rstate=session[constants.RULE_ARG],
                sort=session[constants.SORT_ARG],
                squery=session[constants.SEARCH_ARG],
                order=session[constants.ORDER_ARG],
            )
        )

    # Get allowed rule IDs for the service call
    allowed_rule_ids = get_user_allowed_rule_ids(rule_type_str, session["user_id"], session["user_role_ids"])

    # Use the service to delete the rule
    success, message = rule_service.delete_rule(
        rule_type=enum_rule_type,
        rule_id=rule_id,
        user_id=session["user_id"],
        user_email=session["user_email"],
        org_name=session["user_org"],
        allowed_rule_ids=allowed_rule_ids,
    )

    flash(message, "alert-success" if success else "alert-warning")

    return redirect(
        url_for(
            "dashboard.index",
            rtype=session[constants.TYPE_ARG],
            rstate=session[constants.RULE_ARG],
            sort=session[constants.SORT_ARG],
            squery=session[constants.SEARCH_ARG],
            order=session[constants.ORDER_ARG],
        )
    )


@rules.route("/delete_and_whitelist/<int:rule_type>/<int:rule_id>", methods=["GET"])
@auth_required
@user_or_admin_required
def delete_and_whitelist(rule_type, rule_id):
    """
    Delete an RTBH rule and create a whitelist entry from it.
    """
    if rule_type != RuleTypes.RTBH.value:
        flash("Only RTBH rules can be converted to whitelists", "alert-warning")
        return redirect(url_for("index"))

    # Check if user can modify this rule
    if not check_user_can_modify_rule(rule_id, "rtbh"):
        flash("You cannot delete this rule", "alert-warning")
        return redirect(url_for("index"))

    # Get allowed rule IDs
    allowed_rule_ids = get_user_allowed_rule_ids("rtbh", session["user_id"], session["user_role_ids"])

    # Set whitelist expiration to 7 days from now by default
    whitelist_expires = datetime.now() + timedelta(days=7)

    # Use the service to delete RTBH and create whitelist
    success, messages, whitelist = rule_service.delete_rtbh_and_create_whitelist(
        rule_id=rule_id,
        user_id=session["user_id"],
        org_id=session["user_org_id"],
        user_email=session["user_email"],
        org_name=session["user_org"],
        allowed_rule_ids=allowed_rule_ids,
        whitelist_expires=whitelist_expires,
    )

    for message in messages:
        flash(message, "alert-success" if success else "alert-warning")

    if success and whitelist:
        flash(f"Created whitelist entry ID {whitelist.id} from RTBH rule", "alert-info")

    return redirect(
        url_for(
            "dashboard.index",
            rtype=session[constants.TYPE_ARG],
            rstate=session[constants.RULE_ARG],
            sort=session[constants.SORT_ARG],
            squery=session[constants.SEARCH_ARG],
            order=session[constants.ORDER_ARG],
        )
    )


@rules.route("/group-operation", methods=["POST"])
@auth_required
@user_or_admin_required
def group_operation():
    """
    Delete rules
    """
    dispatch = {"group-update": group_update, "group-delete": group_delete}

    try:
        return dispatch[request.form["action"]]()
    except KeyError:
        flash("Key Error in action dispatching!", "alert-danger")
        return redirect(
            url_for(
                "dashboard.index",
                rtype=session[constants.TYPE_ARG],
                rstate=session[constants.RULE_ARG],
                sort=session[constants.SORT_ARG],
                squery=session[constants.SEARCH_ARG],
                order=session[constants.ORDER_ARG],
            )
        )


@rules.route("/group-delete", methods=["POST"])
@auth_required
@user_or_admin_required
def group_delete():
    """
    Delete rules
    """
    rule_type = session[constants.TYPE_ARG]
    model_name = DATA_MODELS_NAMED[rule_type]
    rule_type_int = constants.RULE_TYPES_DICT[rule_type]
    enum_rule_type = RuleTypes(rule_type_int)
    route_model = ROUTE_MODELS[rule_type_int]

    # Get allowed rules for this user
    allowed_rule_ids = get_user_allowed_rule_ids(rule_type, session["user_id"], session["user_role_ids"])
    allowed_rules_str = [str(x) for x in allowed_rule_ids]

    to_delete = request.form.getlist("delete-id")

    # Check if user has permission to delete these rules
    if set(to_delete).issubset(set(allowed_rules_str)) or is_admin(session["user_roles"]):
        for rule_id in to_delete:
            # withdraw route
            model = db.session.get(model_name, rule_id)
            command = route_model(model, constants.WITHDRAW)
            route = Route(
                author=f"{session['user_email']} / {session['user_org']}",
                source=RouteSources.UI,
                command=command,
            )
            announce_route(route)

            log_withdraw(
                session["user_id"],
                route.command,
                enum_rule_type,
                model.id,
                f"{session['user_email']} / {session['user_org']}",
            )

        db.session.query(model_name).filter(model_name.id.in_(to_delete)).delete(synchronize_session=False)
        db.session.commit()

        flash(f"Rules {to_delete} deleted", "alert-success")
    else:
        flash(f"You can not delete rules {to_delete}", "alert-warning")

    return redirect(
        url_for(
            "dashboard.index",
            rtype=session[constants.TYPE_ARG],
            rstate=session[constants.RULE_ARG],
            sort=session[constants.SORT_ARG],
            squery=session[constants.SEARCH_ARG],
            order=session[constants.ORDER_ARG],
        )
    )


@rules.route("/group-edit", methods=["POST"])
@auth_required
@user_or_admin_required
def group_update():
    """
    update rules
    """
    rule_type = session[constants.TYPE_ARG]
    form_name = DATA_FORMS_NAMED[rule_type]
    to_update = request.form.getlist("delete-id")
    rule_type_int = constants.RULE_TYPES_DICT[rule_type]

    # Get allowed rules for this user
    allowed_rule_ids = get_user_allowed_rule_ids(rule_type, session["user_id"], session["user_role_ids"])
    allowed_rules_str = [str(x) for x in allowed_rule_ids]

    # redirect bad request
    if not set(to_update).issubset(set(allowed_rules_str)) and not is_admin(session["user_roles"]):
        flash("You can't edit these rules!", "alert-danger")
        return redirect(
            url_for(
                "dashboard.index",
                rtype=session[constants.TYPE_ARG],
                rstate=session[constants.RULE_ARG],
                sort=session[constants.SORT_ARG],
                squery=session[constants.SEARCH_ARG],
                order=session[constants.ORDER_ARG],
            )
        )

    # populate the form
    session["group-update"] = to_update
    form = form_name(request.form)
    form.net_ranges = get_user_nets(session["user_id"])
    if rule_type_int > 2:
        form.action.choices = [(g.id, g.name) for g in db.session.query(Action).order_by("name")]
    if rule_type_int == 1:
        form.community.choices = get_user_communities(session["user_role_ids"])

    form.expires.data = datetime.now()
    for field in form:
        if field.name not in ["expires", "csrf_token", "comment"]:
            field.render_kw = {"disabled": "disabled"}

    action_url = url_for("rules.group_update_save", rule_type=rule_type_int)

    return render_template(
        DATA_TEMPLATES[rule_type_int],
        form=form,
        action_url=action_url,
        editing=True,
        title="Group Update",
    )


@rules.route("/group-save-update/<int:rule_type>", methods=["POST"])
@auth_required
@user_or_admin_required
def group_update_save(rule_type):
    # redirect bad request
    try:
        to_update = session["group-update"]
    except KeyError:
        return redirect(
            url_for(
                "dashboard.index",
                rtype=session[constants.TYPE_ARG],
                rstate=session[constants.RULE_ARG],
                sort=session[constants.SORT_ARG],
                squery=session[constants.SEARCH_ARG],
                order=session[constants.ORDER_ARG],
            )
        )

    model_name = DATA_MODELS[rule_type]
    form_name = DATA_FORMS[rule_type]
    enum_rule_type = RuleTypes(rule_type)

    form = form_name(request.form)

    # set new expiration date
    expires = round_to_ten_minutes(form.expires.data)
    # set state by time
    rstate_id = get_state_by_time(form.expires.data)
    comment = form.comment.data
    route_model = ROUTE_MODELS[rule_type]

    for rule_id in to_update:
        # check global limit
        check_gl = check_global_rule_limit(rule_type)
        if rstate_id == 1 and check_gl:
            return redirect(url_for("rules.global_limit_reached", rule_type=rule_type))

        # check if rule will be reactivated
        check = check_rule_limit(session["user_org_id"], rule_type=rule_type)
        if rstate_id == 1 and check:
            return redirect(url_for("rules.limit_reached", rule_type=rule_type))

        # update record
        model = db.session.get(model_name, rule_id)
        model.expires = expires
        model.rstate_id = rstate_id
        model.comment = f"{model.comment} {comment}"
        db.session.commit()

        if model.rstate_id == 1:
            # announce route
            command = route_model(model, constants.ANNOUNCE)
            route = Route(
                author=f"{session['user_email']} / {session['user_org']}",
                source=RouteSources.UI,
                command=command,
            )
            announce_route(route)
            # log changes
            log_route(
                session["user_id"],
                model,
                enum_rule_type,
                f"{session['user_email']} / {session['user_org']}",
            )
        else:
            # withdraw route
            command = route_model(model, constants.WITHDRAW)
            route = Route(
                author=f"{session['user_email']} / {session['user_org']}",
                source=RouteSources.UI,
                command=command,
            )
            announce_route(route)
            # log changes
            log_withdraw(
                session["user_id"],
                route.command,
                enum_rule_type,
                model.id,
                f"{session['user_email']} / {session['user_org']}",
            )

    flash(f"Rules {to_update} successfully updated", "alert-success")

    return redirect(
        url_for(
            "dashboard.index",
            rtype=session[constants.TYPE_ARG],
            rstate=session[constants.RULE_ARG],
            sort=session[constants.SORT_ARG],
            squery=session[constants.SEARCH_ARG],
            order=session[constants.ORDER_ARG],
        )
    )


@rules.route("/add_ipv4_rule", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def ipv4_rule():
    if check_global_rule_limit(RuleTypes.IPv4):
        return redirect(url_for("rules.global_limit_reached", rule_type=RuleTypes.IPv4))

    if check_rule_limit(session["user_org_id"], RuleTypes.IPv4):
        return redirect(url_for("rules.limit_reached", rule_type=RuleTypes.IPv4))

    net_ranges = get_user_nets(session["user_id"])
    form = IPv4Form(request.form)

    # add values to form instance
    user_actions = get_user_actions(session["user_role_ids"])
    user_actions = [
        (0, "---- select action ----"),
    ] + user_actions

    form.action.choices = user_actions
    form.action.default = 0
    form.net_ranges = net_ranges

    if request.method == "POST" and form.validate():
        # Use the service to create/update the rule
        _model, message = rule_service.create_or_update_ipv4_rule(
            form_data=form.data,
            user_id=session["user_id"],
            org_id=session["user_org_id"],
            user_email=session["user_email"],
            org_name=session["user_org"],
        )

        flash(message, "alert-success")

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(hours=1)
    form.expires.data = default_expires

    return render_template("forms/ipv4_rule.html", form=form, action_url=url_for("rules.ipv4_rule"))


@rules.route("/add_ipv6_rule", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def ipv6_rule():
    if check_global_rule_limit(RuleTypes.IPv6):
        return redirect(url_for("rules.global_limit_reached", rule_type=RuleTypes.IPv6))

    if check_rule_limit(session["user_org_id"], RuleTypes.IPv6):
        return redirect(url_for("rules.limit_reached", rule_type=RuleTypes.IPv6))

    net_ranges = get_user_nets(session["user_id"])
    form = IPv6Form(request.form)

    # set up form
    user_actions = get_user_actions(session["user_role_ids"])
    user_actions = [
        (0, "---- select action ----"),
    ] + user_actions
    form.action.choices = user_actions
    form.action.default = 0
    form.net_ranges = net_ranges

    if request.method == "POST" and form.validate():
        _model, message = rule_service.create_or_update_ipv6_rule(
            form_data=form.data,
            user_id=session["user_id"],
            org_id=session["user_org_id"],
            user_email=session["user_email"],
            org_name=session["user_org"],
        )
        flash(message, "alert-success")

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(hours=1)
    form.expires.data = default_expires

    return render_template("forms/ipv6_rule.html", form=form, action_url=url_for("rules.ipv6_rule"))


@rules.route("/add_rtbh_rule", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def rtbh_rule():
    if check_global_rule_limit(RuleTypes.RTBH):
        return redirect(url_for("rules.global_limit_reached", rule_type=RuleTypes.RTBH))

    if check_rule_limit(session["user_org_id"], RuleTypes.RTBH):
        return redirect(url_for("rules.limit_reached", rule_type=RuleTypes.RTBH))

    all_com = db.session.query(Community).all()
    if not all_com:
        insert_initial_communities()

    net_ranges = get_user_nets(session["user_id"])
    user_communities = get_user_communities(session["user_role_ids"])
    # setup form
    form = RTBHForm(request.form)
    user_communities = [
        (0, "---- select community ----"),
    ] + user_communities
    form.community.choices = user_communities
    form.net_ranges = net_ranges
    whitelistable = Community.get_whitelistable_communities(current_app.config["ALLOWED_COMMUNITIES"])

    if request.method == "POST" and form.validate():
        _model, messages = rule_service.create_or_update_rtbh_rule(
            form_data=form.data,
            user_id=session["user_id"],
            org_id=session["user_org_id"],
            user_email=session["user_email"],
            org_name=session["user_org"],
        )
        for message in messages:
            flash(message, "alert-success")

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(days=7)
    form.expires.data = default_expires

    return render_template(
        "forms/rtbh_rule.html", form=form, action_url=url_for("rules.rtbh_rule"), whitelistable=whitelistable
    )


@rules.route("/limit_reached/<rule_type>")
@auth_required
def limit_reached(rule_type):
    rule_type = constants.RULE_NAMES_DICT[int(rule_type)]
    count_4 = db.session.query(Flowspec4).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    count_6 = db.session.query(Flowspec6).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    count_rtbh = db.session.query(RTBH).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    org = db.session.get(Organization, session["user_org_id"])
    return render_template(
        "pages/limit_reached.html",
        message="Your organization limit has been reached.",
        rule_type=rule_type,
        count_4=count_4,
        count_6=count_6,
        count_rtbh=count_rtbh,
        org=org,
    )


@rules.route("/global_limit_reached/<rule_type>")
@auth_required
def global_limit_reached(rule_type):
    rule_type = constants.RULE_NAMES_DICT[int(rule_type)]
    count_4 = db.session.query(Flowspec4).filter_by(rstate_id=1).count()
    count_6 = db.session.query(Flowspec6).filter_by(rstate_id=1).count()
    count_rtbh = db.session.query(RTBH).filter_by(rstate_id=1).count()

    Limit = namedtuple("Limit", ["limit_flowspec4", "limit_flowspec6", "limit_rtbh"])
    limit = Limit(
        limit_flowspec4=current_app.config["FLOWSPEC4_MAX_RULES"],
        limit_flowspec6=current_app.config["FLOWSPEC6_MAX_RULES"],
        limit_rtbh=current_app.config["RTBH_MAX_RULES"],
    )

    return render_template(
        "pages/limit_reached.html",
        message="Global system limit has been reached. Please contact your administrator.",
        rule_type=rule_type,
        count_4=count_4,
        count_6=count_6,
        count_rtbh=count_rtbh,
        org=limit,
    )


@rules.route("/export")
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

    return render_template(
        "pages/dashboard_admin.html",
        rules=rules,
        actions=actions,
        rules_rtbh=rules_rtbh,
        today=datetime.now(),
    )


@rules.route("/announce_all", methods=["GET"])
@localhost_only
def announce_all():
    announce_all_routes(constants.ANNOUNCE)
    return " "


@rules.route("/withdraw_expired", methods=["GET"])
@localhost_only
def withdraw_expired():
    """
    Cleaning endpoint:
    - Deletes expired whitelists
    - Withdraws all expired routes from ExaBGP
    - Deletes old expired rules
    - Deletes logs older than 30 days
    """
    # Delete expired whitelists
    whitelist_messages = delete_expired_whitelists()
    for msg in whitelist_messages:
        current_app.logger.info(msg)

    # Withdraw expired routes
    announce_all_routes(constants.WITHDRAW)

    # Delete old expired rules (in batches if needed)
    deletion_counts = rule_service.delete_expired_rules()
    current_app.logger.info(f"Deleted rules: {deletion_counts}")

    # Delete old logs
    Log.delete_old()

    return "Cleanup completed"
