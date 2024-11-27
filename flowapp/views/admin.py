# flowapp/views/admin.py
from datetime import datetime, timedelta
import secrets

from flask import Blueprint, render_template, redirect, flash, request, session, url_for
from sqlalchemy.exc import IntegrityError

from ..forms import ASPathForm, MachineApiKeyForm, UserForm, ActionForm, OrganizationForm, CommunityForm
from ..models import (
    ASPath,
    MachineApiKey,
    User,
    Action,
    Organization,
    Role,
    insert_user,
    get_existing_action,
    Community,
    get_existing_community,
    Log,
)
from ..auth import auth_required, admin_required
from flowapp import db

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/log", methods=["GET"], defaults={"page": 1})
@admin.route("/log/<int:page>", methods=["GET"])
@auth_required
@admin_required
def log(page):
    """
    Displays logs for last two days
    """
    per_page = 20
    now = datetime.now()
    week_ago = now - timedelta(weeks=1)
    logs = (
        Log.query.order_by(Log.time.desc())
        .filter(Log.time > week_ago)
        .paginate(page=page, per_page=per_page, max_per_page=None, error_out=False)
    )
    return render_template("pages/logs.html", logs=logs)


@admin.route("/machine_keys", methods=["GET"])
@auth_required
@admin_required
def machine_keys():
    """
    Display all machine keys, from all admins
    """
    keys = db.session.query(MachineApiKey).all()

    return render_template("pages/machine_api_key.html", keys=keys)


@admin.route("/add_machine_key", methods=["GET", "POST"])
@auth_required
@admin_required
def add_machine_key():
    """
    Add new MachnieApiKey
    :return: form or redirect to list of keys
    """
    generated = secrets.token_hex(24)
    form = MachineApiKeyForm(request.form, key=generated)

    if request.method == "POST" and form.validate():
        print("Form validated")
        # import ipdb; ipdb.set_trace()
        model = MachineApiKey(
            machine=form.machine.data,
            key=form.key.data,
            expires=form.expires.data,
            readonly=form.readonly.data,
            comment=form.comment.data,
            user_id=session["user_id"],
        )

        db.session.add(model)
        db.session.commit()
        flash("NewKey saved", "alert-success")

        return redirect(url_for("admin.machine_keys"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    return render_template("forms/machine_api_key.html", form=form, generated_key=generated)


@admin.route("/delete_machine_key/<int:key_id>", methods=["GET"])
@auth_required
@admin_required
def delete_machine_key(key_id):
    """
    Delete api_key and machine
    :param key_id: integer
    """
    model = db.session.query(MachineApiKey).get(key_id)
    # delete from db
    db.session.delete(model)
    db.session.commit()
    flash("Key deleted", "alert-success")

    return redirect(url_for("admin.machine_keys"))


@admin.route("/user", methods=["GET", "POST"])
@auth_required
@admin_required
def user():
    form = UserForm(request.form)
    form.role_ids.choices = [(g.id, g.name) for g in db.session.query(Role).order_by("name")]
    form.org_ids.choices = [(g.id, g.name) for g in db.session.query(Organization).order_by("name")]

    if request.method == "POST" and form.validate():
        # test if user is unique
        exist = db.session.query(User).filter_by(uuid=form.uuid.data).first()
        if not exist:
            insert_user(
                uuid=form.uuid.data,
                name=form.name.data,
                phone=form.phone.data,
                email=form.email.data,
                comment=form.comment.data,
                role_ids=form.role_ids.data,
                org_ids=form.org_ids.data,
            )
            flash("User saved")
            return redirect(url_for("admin.users"))
        else:
            flash("User {} already exists".format(form.email.data), "alert-danger")

    action_url = url_for("admin.user")
    return render_template(
        "forms/simple_form.html",
        title="Add new user to Flowspec",
        form=form,
        action_url=action_url,
    )


@admin.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_user(user_id):
    user = db.session.query(User).get(user_id)
    form = UserForm(request.form, obj=user)
    form.role_ids.choices = [(g.id, g.name) for g in db.session.query(Role).order_by("name")]
    form.org_ids.choices = [(g.id, g.name) for g in db.session.query(Organization).order_by("name")]

    if request.method == "POST" and form.validate():
        user.update(form)
        return redirect(url_for("admin.users"))

    form.role_ids.data = [role.id for role in user.role]
    form.org_ids.data = [org.id for org in user.organization]
    action_url = url_for("admin.edit_user", user_id=user_id)

    return render_template(
        "forms/simple_form.html",
        title="Editing {}".format(user.email),
        form=form,
        action_url=action_url,
    )


@admin.route("/user/delete/<int:user_id>", methods=["GET"])
@auth_required
@admin_required
def delete_user(user_id):
    user = db.session.query(User).get(user_id)
    username = user.email
    db.session.delete(user)

    message = "User {} deleted".format(username)
    alert_type = "alert-success"
    try:
        db.session.commit()
    except IntegrityError as e:
        message = "User {} owns some rules, can not be deleted!".format(username)
        alert_type = "alert-danger"
        print(e)

    flash(message, alert_type)
    return redirect(url_for("admin.users"))


@admin.route("/users")
@auth_required
@admin_required
def users():
    users = User.query.all()
    return render_template("pages/users.html", users=users)


@admin.route("/organizations")
@auth_required
@admin_required
def organizations():
    orgs = db.session.query(Organization).all()
    return render_template("pages/orgs.html", orgs=orgs)


@admin.route("/organization", methods=["GET", "POST"])
@auth_required
@admin_required
def organization():
    form = OrganizationForm(request.form)

    if request.method == "POST" and form.validate():
        # test if user is unique
        exist = db.session.query(Organization).filter_by(name=form.name.data).first()
        if not exist:
            org = Organization(name=form.name.data, arange=form.arange.data)
            db.session.add(org)
            db.session.commit()
            flash("Organization saved")
            return redirect(url_for("admin.organizations"))
        else:
            flash("Organization {} already exists".format(form.name.data), "alert-danger")

    action_url = url_for("admin.organization")
    return render_template(
        "forms/simple_form.html",
        title="Add new organization to Flowspec",
        form=form,
        action_url=action_url,
    )


@admin.route("/organization/edit/<int:org_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_organization(org_id):
    org = db.session.query(Organization).get(org_id)
    form = OrganizationForm(request.form, obj=org)

    if request.method == "POST" and form.validate():
        form.populate_obj(org)
        db.session.commit()
        flash("Organization updated")
        return redirect(url_for("admin.organizations"))

    action_url = url_for("admin.edit_organization", org_id=org.id)
    return render_template(
        "forms/simple_form.html",
        title="Editing {}".format(org.name),
        form=form,
        action_url=action_url,
    )


@admin.route("/organization/delete/<int:org_id>", methods=["GET"])
@auth_required
@admin_required
def delete_organization(org_id):
    org = db.session.query(Organization).get(org_id)
    aname = org.name
    db.session.delete(org)
    message = "Organization {} deleted".format(aname)
    alert_type = "alert-success"
    try:
        db.session.commit()
    except IntegrityError:
        message = "Organization {} has some users, can not be deleted!".format(aname)
        alert_type = "alert-danger"

    flash(message, alert_type)
    db.session.commit()

    return redirect(url_for("admin.organizations"))


@admin.route("/as-paths")
@auth_required
@admin_required
def as_paths():
    mpaths = db.session.query(ASPath).all()
    return render_template("pages/as_paths.html", paths=mpaths)


@admin.route("/as-path", methods=["GET", "POST"])
@auth_required
@admin_required
def as_path():
    form = ASPathForm(request.form)

    if request.method == "POST" and form.validate():
        # test if user is unique
        exist = db.session.query(ASPath).filter_by(prefix=form.prefix.data).first()
        if not exist:
            pth = ASPath(prefix=form.prefix.data, as_path=form.as_path.data)
            db.session.add(pth)
            db.session.commit()
            flash("AS-path saved")
            return redirect(url_for("admin.as_paths"))
        else:
            flash("Prefix {} already taken".format(form.prefix.data), "alert-danger")

    action_url = url_for("admin.as_path")
    return render_template(
        "forms/simple_form.html",
        title="Add new AS-path to Flowspec",
        form=form,
        action_url=action_url,
    )


@admin.route("/as-path/edit/<int:path_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_as_path(path_id):
    pth = db.session.query(ASPath).get(path_id)
    form = ASPathForm(request.form, obj=pth)

    if request.method == "POST" and form.validate():
        form.populate_obj(pth)
        db.session.commit()
        flash("AS-path updated")
        return redirect(url_for("admin.as_paths"))

    action_url = url_for("admin.edit_as_path", path_id=pth.id)
    return render_template(
        "forms/simple_form.html",
        title="Editing {}".format(pth.prefix),
        form=form,
        action_url=action_url,
    )


@admin.route("/as-path/delete/<int:path_id>", methods=["GET"])
@auth_required
@admin_required
def delete_as_path(path_id):
    pth = db.session.query(ASPath).get(path_id)
    db.session.delete(pth)
    message = f"AS path {pth.prefix} : {pth.as_path} deleted"
    alert_type = "alert-success"

    flash(message, alert_type)
    db.session.commit()

    return redirect(url_for("admin.as_paths"))


@admin.route("/actions")
@auth_required
@admin_required
def actions():
    actions = db.session.query(Action).all()
    return render_template("pages/actions.html", actions=actions)


@admin.route("/action", methods=["GET", "POST"])
@auth_required
@admin_required
def action():
    form = ActionForm(request.form)

    if request.method == "POST" and form.validate():
        # test if Acttion is unique
        exist = get_existing_action(form.name.data, form.command.data)
        if not exist:
            action = Action(
                name=form.name.data,
                command=form.command.data,
                description=form.description.data,
                role_id=form.role_id.data,
            )
            db.session.add(action)
            db.session.commit()
            flash("Action saved", "alert-success")
            return redirect(url_for("admin.actions"))
        else:
            flash(
                "Action with name {} or command {} already exists".format(form.name.data, form.command.data),
                "alert-danger",
            )

    action_url = url_for("admin.action")
    return render_template(
        "forms/simple_form.html",
        title="Add new action to Flowspec",
        form=form,
        action_url=action_url,
    )


@admin.route("/action/edit/<int:action_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_action(action_id):
    action = db.session.query(Action).get(action_id)
    print(action.role_id)
    form = ActionForm(request.form, obj=action)
    if request.method == "POST" and form.validate():
        form.populate_obj(action)
        db.session.commit()
        flash("Action updated")
        return redirect(url_for("admin.actions"))

    action_url = url_for("admin.edit_action", action_id=action.id)
    return render_template(
        "forms/simple_form.html",
        title="Editing {}".format(action.name),
        form=form,
        action_url=action_url,
    )


@admin.route("/action/delete/<int:action_id>", methods=["GET"])
@auth_required
@admin_required
def delete_action(action_id):
    action = db.session.query(Action).get(action_id)
    aname = action.name
    db.session.delete(action)

    message = "Action {} deleted".format(aname)
    alert_type = "alert-success"
    try:
        db.session.commit()
    except IntegrityError:
        message = "Action {} is in use in some rules, can not be deleted!".format(aname)
        alert_type = "alert-danger"

    flash(message, alert_type)
    return redirect(url_for("admin.actions"))


@admin.route("/communities")
@auth_required
@admin_required
def communities():
    communities = db.session.query(Community).all()
    return render_template("pages/communities.html", communities=communities)


@admin.route("/community", methods=["GET", "POST"])
@auth_required
@admin_required
def community():
    form = CommunityForm(request.form)

    if request.method == "POST" and form.validate():
        # test if Coomunity name is unique
        exist = get_existing_community(form.name.data)
        if not exist:
            community = Community(
                name=form.name.data,
                comm=form.comm.data,
                larcomm=form.larcomm.data,
                extcomm=form.extcomm.data,
                description=form.description.data,
                as_path=form.as_path.data,
                role_id=form.role_id.data,
            )
            db.session.add(community)
            db.session.commit()
            flash("Community saved", "alert-success")
            return redirect(url_for("admin.communities"))
        else:
            flash(f"Community with name {form.name.data} already exists", "alert-danger")

    community_url = url_for("admin.community")
    return render_template(
        "forms/simple_form.html",
        title="Add new community to Flowspec",
        form=form,
        community_url=community_url,
    )


@admin.route("/community/edit/<int:community_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_community(community_id):
    community = db.session.query(Community).get(community_id)
    print(community.role_id)
    form = CommunityForm(request.form, obj=community)
    if request.method == "POST" and form.validate():
        form.populate_obj(community)
        db.session.commit()
        flash("Community updated")
        return redirect(url_for("admin.communities"))

    community_url = url_for("admin.edit_community", community_id=community.id)
    return render_template(
        "forms/simple_form.html",
        title="Editing {}".format(community.name),
        form=form,
        community_url=community_url,
    )


@admin.route("/community/delete/<int:community_id>", methods=["GET"])
@auth_required
@admin_required
def delete_community(community_id):
    community = db.session.query(Community).get(community_id)
    aname = community.name
    db.session.delete(community)
    message = "Community {} deleted".format(aname)
    alert_type = "alert-success"
    try:
        db.session.commit()
    except IntegrityError:
        message = "Community {} is in use in some rules, can not be deleted!".format(aname)
        alert_type = "alert-danger"

    flash(message, alert_type)
    return redirect(url_for("admin.communities"))
