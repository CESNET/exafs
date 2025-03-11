from datetime import datetime, timedelta
from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from flowapp.auth import (
    auth_required,
    user_or_admin_required,
)
from flowapp.forms import WhitelistForm
from flowapp.models import (
    get_user_nets,
)
from flowapp.services import create_or_update_whitelist

whitelist = Blueprint("whitelist", __name__, template_folder="templates")


@whitelist.route("/add", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def add():
    net_ranges = get_user_nets(session["user_id"])
    form = WhitelistForm(request.form)

    form.net_ranges = net_ranges

    if request.method == "POST" and form.validate():
        model, message = create_or_update_whitelist(
            form.data,
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

    print("NOW", datetime.now())
    default_expires = datetime.now() + timedelta(hours=1)
    form.expires.data = default_expires

    return render_template("forms/whitelist.html", form=form, action_url=url_for("whitelist.add"))
