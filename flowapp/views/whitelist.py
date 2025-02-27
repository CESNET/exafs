from datetime import datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from flowapp import constants, db, messages
from flowapp.auth import (
    auth_required,
    user_or_admin_required,
)
from flowapp.constants import RuleTypes
from flowapp.forms import WhitelistForm
from flowapp.models import (
    Whitelist,
    get_user_nets,
)
from flowapp.output import ROUTE_MODELS, announce_route, log_route, log_withdraw, RouteSources, Route
from flowapp.utils import (
    flash_errors,
    get_state_by_time,
    quote_to_ent,
    round_to_ten_minutes,
)

whitelist = Blueprint("whitelist", __name__, template_folder="templates")


@whitelist.route("/add", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def add():
    net_ranges = get_user_nets(session["user_id"])
    form = WhitelistForm(request.form)

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

    print("NOW", datetime.now())
    default_expires = datetime.now() + timedelta(hours=1)
    form.expires.data = default_expires

    return render_template("forms/ipv4_rule.html", form=form, action_url=url_for("rules.ipv4_rule"))
