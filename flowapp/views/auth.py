from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import login_user, logout_user
from passlib.context import CryptContext

from flowapp import db
from flowapp.forms import LoginForm
from flowapp.models import AuthUser, User

auth = Blueprint("auth", __name__, template_folder="templates")


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST" and form.validate():
        user = db.session.query(User).filter_by(uuid=form.email.data).first()
        auth_user = db.session.query(AuthUser).filter_by(email=form.email.data).first()
        if user is not None and _validate_password(auth_user, form.password.data):
            login_user(auth_user, remember=form.remember.data)
            flash("Logged in successfully!", "alert-success")
            return redirect(url_for("index"))
        else:
            flash("Unknown e-mail or invalid password.", "alert-danger")

    return render_template("forms/login.j2", form=form)


@auth.route("/logout", methods=["GET"])
def logout():
    logout_user()
    del session["user_email"]
    del session["user_id"]
    del session["user_roles"]
    del session["user_orgs"]
    del session["user_role_ids"]
    del session["user_org_ids"]
    del session["can_edit"]
    flash("You have been logged out.", "alert-info")
    return redirect(url_for("index"))


def _validate_password(user: AuthUser, password: str) -> bool:
    """Validate a password for a given user.

    Parameters
    ----------
    user: AuthUser
        Email to validate password for.
    password: str
        Provided password to validate.

    Returns
    -------
    bool
        True if user and password match, False if there is a mismatch,
        the user does not exist or the password hash algorithm set
        in the config file is invalid.
    """

    if user is None:
        return False
    hash_algo = current_app.config.get("AUTH_PASSWORD_HASH_ALGO", "none")

    if hash_algo.lower() == "none":
        return password == user.password_hash
    else:
        try:
            ctx = CryptContext(schemes=[hash_algo])
            return ctx.verify(password, hash_algo)
        except ValueError:
            print("Invalid hash algorithm, skipping password validation!")
            return False
