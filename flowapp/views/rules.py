# flowapp/views/admin.py
from datetime import datetime, timedelta
from operator import ge, lt
from collections import namedtuple

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from flowapp import constants, db, messages
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
    get_ipv4_model_if_exists,
    get_ipv6_model_if_exists,
    get_rtbh_model_if_exists,
    get_user_actions,
    get_user_communities,
    get_user_nets,
    insert_initial_communities,
)
from flowapp.output import ROUTE_MODELS, announce_route, log_route, log_withdraw, RouteSources, Route
from flowapp.utils import (
    flash_errors,
    get_state_by_time,
    quote_to_ent,
    round_to_ten_minutes,
)

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
    :param rule_type: string - type of rule
    :param rule_id: integer - id of the rule
    """
    model_name = DATA_MODELS[rule_type]
    form_name = DATA_FORMS[rule_type]

    model = db.session.query(model_name).get(rule_id)
    form = form_name(request.form, obj=model)
    form.net_ranges = get_user_nets(session["user_id"])

    if rule_type > 2:
        form.action.choices = [(g.id, g.name) for g in db.session.query(Action).order_by("name")]
        form.action.data = model.action_id

    if rule_type == 1:
        form.community.choices = get_user_communities(session["user_role_ids"])
        form.community.data = model.community_id

    if rule_type == 4:
        form.protocol.data = model.protocol

    if rule_type == 6:
        form.next_header.data = model.next_header

    # do not need to validate - all is readonly
    if request.method == "POST":
        # check if rule will be reactivated
        state = get_state_by_time(form.expires.data)

        # check global limit
        check_gl = check_global_rule_limit(rule_type)
        if state == 1 and check_gl:
            return redirect(url_for("rules.global_limit_reached", rule_type=rule_type))
        # check org limit
        if state == 1 and check_rule_limit(session["user_org_id"], rule_type=rule_type):
            return redirect(url_for("rules.limit_reached", rule_type=rule_type))

        # set new expiration date
        model.expires = round_to_ten_minutes(form.expires.data)
        # set again the active state
        model.rstate_id = get_state_by_time(form.expires.data)
        model.comment = form.comment.data
        db.session.commit()
        flash("Rule successfully updated", "alert-success")

        route_model = ROUTE_MODELS[rule_type]

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
                rule_type,
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
                rule_type,
                model.id,
                f"{session['user_email']} / {session['user_org']}",
            )

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
    :param sort_key:
    :param filter_text:
    :param rstate:
    :param rule_type: string - type of rule to be deleted
    :param rule_id: integer - rule id
    """
    model_name = DATA_MODELS[rule_type]
    route_model = ROUTE_MODELS[rule_type]

    model = db.session.query(model_name).get(rule_id)
    if model.id in session[constants.RULES_KEY]:
        # withdraw route
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
            rule_type,
            model.id,
            f"{session['user_email']} / {session['user_org']}",
        )

        # delete from db
        db.session.delete(model)
        db.session.commit()
        flash("Rule deleted", "alert-success")

    else:
        flash("You can not delete this rule", "alert-warning")

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
    route_model = ROUTE_MODELS[rule_type_int]
    rules = [str(x) for x in session[constants.RULES_KEY]]
    to_delete = request.form.getlist("delete-id")

    if set(to_delete).issubset(set(rules)) or is_admin(session["user_roles"]):
        for rule_id in to_delete:
            # withdraw route
            model = db.session.query(model_name).get(rule_id)
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
                rule_type_int,
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
    rule_type = session[constants.TYPE_ARG]
    rule_type_int = constants.RULE_TYPES_DICT[rule_type]
    rules = [str(x) for x in session[constants.RULES_KEY]]
    # redirect bad request
    if not set(to_update).issubset(set(rules)) or is_admin(session["user_roles"]):
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
        model = db.session.query(model_name).get(rule_id)
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
                rule_type,
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
                rule_type,
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
        model = get_ipv4_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(form.expires.data)
            flash_message = "Existing IPv4 Rule found. Expiration time was updated to new value."
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
                user_id=session["user_id"],
                org_id=session["user_org_id"],
                rstate_id=get_state_by_time(form.expires.data),
            )
            flash_message = "IPv4 Rule saved"
            db.session.add(model)

        db.session.commit()
        flash(flash_message, "alert-success")

        # announce route if model is in active state
        if model.rstate_id == 1:
            command = messages.create_ipv4(model, constants.ANNOUNCE)
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
            RuleTypes.IPv4,
            f"{session['user_email']} / {session['user_org']}",
        )

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(days=7)
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
        model = get_ipv6_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(form.expires.data)
            flash_message = "Existing IPv4 Rule found. Expiration time was updated to new value."
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
                expires=round_to_ten_minutes(form.expires.data),
                comment=quote_to_ent(form.comment.data),
                action_id=form.action.data,
                user_id=session["user_id"],
                org_id=session["user_org_id"],
                rstate_id=get_state_by_time(form.expires.data),
            )
            flash_message = "IPv6 Rule saved"
            db.session.add(model)

        db.session.commit()
        flash(flash_message, "alert-success")

        # announce routes
        if model.rstate_id == 1:
            command = messages.create_ipv6(model, constants.ANNOUNCE)
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
            RuleTypes.IPv6,
            f"{session['user_email']} / {session['user_org']}",
        )

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(days=7)
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

    if request.method == "POST" and form.validate():
        model = get_rtbh_model_if_exists(form.data, 1)

        if model:
            model.expires = round_to_ten_minutes(form.expires.data)
            flash_message = "Existing RTBH Rule found. Expiration time was updated to new value."
        else:
            model = RTBH(
                ipv4=form.ipv4.data,
                ipv4_mask=form.ipv4_mask.data,
                ipv6=form.ipv6.data,
                ipv6_mask=form.ipv6_mask.data,
                community_id=form.community.data,
                expires=round_to_ten_minutes(form.expires.data),
                comment=quote_to_ent(form.comment.data),
                user_id=session["user_id"],
                org_id=session["user_org_id"],
                rstate_id=get_state_by_time(form.expires.data),
            )
            db.session.add(model)
            db.session.commit()
            flash_message = "RTBH Rule saved"

        flash(flash_message, "alert-success")
        # announce routes
        if model.rstate_id == 1:
            command = messages.create_rtbh(model, constants.ANNOUNCE)
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
            RuleTypes.RTBH,
            f"{session['user_email']} / {session['user_org']}",
        )

        return redirect(url_for("index"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    default_expires = datetime.now() + timedelta(days=7)
    form.expires.data = default_expires

    return render_template("forms/rtbh_rule.html", form=form, action_url=url_for("rules.rtbh_rule"))


@rules.route("/limit_reached/<rule_type>")
@auth_required
def limit_reached(rule_type):
    rule_type = constants.RULE_NAMES_DICT[int(rule_type)]
    count_4 = db.session.query(Flowspec4).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    count_6 = db.session.query(Flowspec6).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    count_rtbh = db.session.query(RTBH).filter_by(rstate_id=1, org_id=session["user_org_id"]).count()
    org = db.session.query(Organization).get(session["user_org_id"])
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
    announce_all_routes(constants.WITHDRAW)
    return " "


def announce_all_routes(action=constants.ANNOUNCE):
    """
    get routes from db and send it to ExaBGB api

    @TODO take the request away, use some kind of messaging (maybe celery?)
    :param action: action with routes - announce valid routes or withdraw expired routes
    """
    today = datetime.now()
    comp_func = ge if action == constants.ANNOUNCE else lt

    rules4 = (
        db.session.query(Flowspec4)
        .filter(Flowspec4.rstate_id == 1)
        .filter(comp_func(Flowspec4.expires, today))
        .order_by(Flowspec4.expires.desc())
        .all()
    )
    rules6 = (
        db.session.query(Flowspec6)
        .filter(Flowspec6.rstate_id == 1)
        .filter(comp_func(Flowspec6.expires, today))
        .order_by(Flowspec6.expires.desc())
        .all()
    )
    rules_rtbh = (
        db.session.query(RTBH)
        .filter(RTBH.rstate_id == 1)
        .filter(comp_func(RTBH.expires, today))
        .order_by(RTBH.expires.desc())
        .all()
    )

    messages_v4 = [messages.create_ipv4(rule, action) for rule in rules4]
    messages_v6 = [messages.create_ipv6(rule, action) for rule in rules6]
    messages_rtbh = [messages.create_rtbh(rule, action) for rule in rules_rtbh]

    messages_all = []
    messages_all.extend(messages_v4)
    messages_all.extend(messages_v6)
    messages_all.extend(messages_rtbh)

    author_action = "announce all" if action == constants.ANNOUNCE else "withdraw all expired"

    for command in messages_all:
        route = Route(
            author=f"System call / {author_action} rules",
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)

    if action == constants.WITHDRAW:
        for ruleset in [rules4, rules6, rules_rtbh]:
            for rule in ruleset:
                rule.rstate_id = 2

        db.session.commit()
