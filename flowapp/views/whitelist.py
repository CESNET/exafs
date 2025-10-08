from datetime import datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from flowapp.auth import (
    auth_required,
    user_or_admin_required,
)
from flowapp import constants, db
from flowapp.forms import WhitelistForm
from flowapp.models import get_user_nets, Whitelist
from flowapp.services import create_or_update_whitelist, delete_whitelist
from flowapp.utils.base import flash_errors
from flowapp.auth import check_user_can_modify_rule


whitelist = Blueprint("whitelist", __name__, template_folder="templates")


@whitelist.route("/add", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def add():
    net_ranges = get_user_nets(session["user_id"])
    form = WhitelistForm(request.form)

    form.net_ranges = net_ranges

    if request.method == "POST" and form.validate():
        model, messages = create_or_update_whitelist(
            form.data,
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

    default_expires = datetime.now() + timedelta(hours=1)
    form.expires.data = default_expires

    return render_template("forms/whitelist.html", form=form, action_url=url_for("whitelist.add"))


@whitelist.route("/reactivate/<int:wl_id>", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def reactivate(wl_id):
    """
    Set new time for whitelist
    :param wl_id: int - id of the whitelist
    """

    model = db.session.get(Whitelist, wl_id)
    form = WhitelistForm(request.form, obj=model)
    form.net_ranges = get_user_nets(session["user_id"])

    # do not need to validate - all is readonly
    if request.method == "POST":
        model = create_or_update_whitelist(
            form.data,
            user_id=session["user_id"],
            org_id=session["user_org_id"],
            user_email=session["user_email"],
            org_name=session["user_org"],
        )
        flash("Whitelist updated", "alert-success")
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

    action_url = url_for("whitelist.reactivate", wl_id=wl_id)

    return render_template(
        "forms/whitelist.html",
        form=form,
        action_url=action_url,
        editing=True,
        title="Update",
    )


@whitelist.route("/delete/<int:wl_id>", methods=["GET"])
@auth_required
@user_or_admin_required
def delete(wl_id):
    """
    Delete whitelist
    :param wl_id: integer - id of the whitelist
    """
    # Check if user can modify this whitelist
    if check_user_can_modify_rule(wl_id, "whitelist"):
        messages = delete_whitelist(wl_id)
        flash(f"Whitelist {wl_id} deleted", "alert-success")
        for message in messages:
            flash(message, "alert-info")
    else:
        flash("You can not delete this Whitelist", "alert-warning")

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
