import csv
from io import StringIO
from datetime import datetime, timedelta
import secrets

from sqlalchemy import func, text
from flask import Blueprint, render_template, redirect, flash, request, session, url_for, current_app
import sqlalchemy
from sqlalchemy.exc import IntegrityError, OperationalError

from ..forms import ASPathForm, BulkUserForm, MachineApiKeyForm, UserForm, ActionForm, OrganizationForm, CommunityForm
from ..models import (
    ASPath,
    ApiKey,
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
    Flowspec4,
    Flowspec6,
    RTBH,
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
    form.user.choices = [(g.id, f"{g.name} ({g.uuid})") for g in db.session.query(User).order_by("name")]

    if request.method == "POST" and form.validate():
        target_user = db.session.get(User, form.user.data)
        target_org = target_user.organization.first() if target_user else None
        current_user = session.get("user_name")
        curent_email = session.get("user_uuid")
        comment = f"created by: {current_user}/{curent_email}, comment: {form.comment.data}"
        model = MachineApiKey(
            machine=form.machine.data,
            key=form.key.data,
            expires=form.expires.data,
            readonly=form.readonly.data,
            comment=comment,
            user_id=target_user.id,
            org_id=target_org.id,
        )

        db.session.add(model)
        db.session.commit()
        flash("NewKey saved", "alert-success")

        return redirect(url_for("admin.machine_keys"))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.debug("Error in the %s field - %s" % (getattr(form, field).label.text, error))

    return render_template("forms/machine_api_key.html", form=form, generated_key=generated)


@admin.route("/delete_machine_key/<int:key_id>", methods=["GET"])
@auth_required
@admin_required
def delete_machine_key(key_id):
    """
    Delete api_key and machine
    :param key_id: integer
    """
    model = db.session.get(MachineApiKey, key_id)
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
    user = db.session.get(User, user_id)
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
        title=f"Editing {user.email}",
        form=form,
        action_url=action_url,
    )


@admin.route("/user/delete/<int:user_id>", methods=["GET"])
@auth_required
@admin_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "alert-danger")
        return redirect(url_for("admin.users"))

    username = user.email
    db.session.delete(user)

    message = f"User {username} deleted"
    alert_type = "alert-success"

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()  # Rollback on IntegrityError
        message = f"User {username} owns some rules, cannot be deleted! Delete rules first."
        alert_type = "alert-danger"
    except OperationalError:
        db.session.rollback()  # Rollback on OperationalError
        message = f"User {username} owns some rules, cannot be deleted! Delete rules first."
        alert_type = "alert-danger"

    flash(message, alert_type)
    return redirect(url_for("admin.users"))


@admin.route("/users")
@auth_required
@admin_required
def users():
    users = User.query.all()
    return render_template("pages/users.html", users=users)


@admin.route("/bulk-import-users", methods=["GET"])
@auth_required
@admin_required
def bulk_import_users():
    form = BulkUserForm(request.form)
    orgs = db.session.execute(db.select(Organization).order_by(Organization.name)).scalars()
    return render_template("forms/bulk_user_form.html", form=form, orgs=orgs)


@admin.route("/bulk-import-users", methods=["POST"])
@auth_required
@admin_required
def bulk_import_users_save():
    form = BulkUserForm(request.form)
    roles = [role.id for role in db.session.query(Role).all()]
    orgs = [org.id for org in db.session.query(Organization).all()]
    uuids = [user.uuid for user in db.session.query(User).all()]
    form.roles = roles
    form.organizations = orgs
    form.uuids = uuids

    if request.method == "POST" and form.validate():
        # Get CSV data from textarea
        csv_data = form.users.data
        # Parse CSV data
        csv_reader = csv.DictReader(StringIO(csv_data), delimiter=",")
        errored = False
        for row in csv_reader:
            try:
                # Extract and prepare data
                uuid = row["uuid-eppn"]
                name = row["name"]
                phone = row["telefon"]
                email = row["email"]

                # Convert role and organization fields to lists of integers
                role_ids = [int(row["role"])]  # role_id should be a list
                org_ids = [int(row["organizace"])]  # org_id should be a list
                notice = row["poznamka"]

                # Insert user
                insert_user(
                    uuid=uuid, role_ids=role_ids, org_ids=org_ids, name=name, phone=phone, email=email, comment=notice
                )
            except KeyError as e:
                errored = True
                # Handle missing fields or other errors in the CSV
                flash(f"Missing field in CSV: {e}", "alert-danger")
            except ValueError as e:
                errored = True
                # Handle conversion issues (like invalid int for role/org)
                flash(f"Data conversion error: {e}", "alert-danger")
            except sqlalchemy.exc.IntegrityError as e:
                errored = True
                db.session.rollback()
                flash(f"SQL Integrity error: {e}", "alert-danger")

        if not errored:
            return redirect(url_for("admin.users"))

    return render_template("forms/bulk_user_form.html", form=form)


@admin.route("/organizations")
@auth_required
@admin_required
def organizations():
    # Query all organizations and eager load RTBH relationships
    orgs = db.session.query(Organization).options(db.joinedload(Organization.rtbh)).all()

    # Get RTBH counts with rstate_id=1 for all organizations in one query
    rtbh_counts_query = (
        db.session.query(RTBH.org_id, func.count(RTBH.id)).filter(RTBH.rstate_id == 1).group_by(RTBH.org_id).all()
    )

    flowspec4_count_query = (
        db.session.query(Flowspec4.org_id, func.count(Flowspec4.id))
        .filter(Flowspec4.rstate_id == 1)
        .group_by(Flowspec4.org_id)
        .all()
    )

    flowspec6_count_query = (
        db.session.query(Flowspec6.org_id, func.count(Flowspec6.id))
        .filter(Flowspec6.rstate_id == 1)
        .group_by(Flowspec6.org_id)
        .all()
    )

    flowspec4_all_count = db.session.query(Flowspec4).filter(Flowspec4.rstate_id == 1).count()
    flowspec6_all_count = db.session.query(Flowspec6).filter(Flowspec6.rstate_id == 1).count()
    rtbh_all_count = db.session.query(RTBH).filter(RTBH.rstate_id == 1).count()

    # Convert query result to a dictionary {org_id: count}
    rtbh_counts = {org_id: count for org_id, count in rtbh_counts_query}
    flowspec4_counts = {org_id: count for org_id, count in flowspec4_count_query}
    flowspec6_counts = {org_id: count for org_id, count in flowspec6_count_query}

    return render_template(
        "pages/orgs.html",
        orgs=orgs,
        rtbh_counts=rtbh_counts,
        flowspec4_counts=flowspec4_counts,
        flowspec6_counts=flowspec6_counts,
        rtbh_all_count=rtbh_all_count,
        flowspec4_all_count=flowspec4_all_count,
        flowspec6_all_count=flowspec6_all_count,
        flowspec4_limit=current_app.config.get("FLOWSPEC4_MAX_RULES", 9000),
        flowspec6_limit=current_app.config.get("FLOWSPEC6_MAX_RULES", 9000),
        rtbh_limit=current_app.config.get("RTBH_MAX_RULES", 100000),
    )


@admin.route("/organization", methods=["GET", "POST"])
@auth_required
@admin_required
def organization():
    form = OrganizationForm(request.form)

    if request.method == "POST" and form.validate():
        # test if user is unique
        exist = db.session.query(Organization).filter_by(name=form.name.data).first()
        if not exist:
            org = Organization(
                name=form.name.data,
                arange=form.arange.data,
                limit_flowspec4=form.limit_flowspec4.data,
                limit_flowspec6=form.limit_flowspec6.data,
                limit_rtbh=form.limit_rtbh.data,
            )
            db.session.add(org)
            db.session.commit()
            flash("Organization saved")
            return redirect(url_for("admin.organizations"))
        else:
            flash("Organization {} already exists".format(form.name.data), "alert-danger")

    action_url = url_for("admin.organization")
    return render_template(
        "forms/org.html",
        title="Add new organization to Flowspec",
        form=form,
        action_url=action_url,
    )


@admin.route("/organization/edit/<int:org_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_organization(org_id):
    org = db.session.get(Organization, org_id)
    form = OrganizationForm(request.form, obj=org)

    if request.method == "POST" and form.validate():
        form.populate_obj(org)
        db.session.commit()
        flash("Organization updated", "alert-success")
        return redirect(url_for("admin.organizations"))

    action_url = url_for("admin.edit_organization", org_id=org.id)
    return render_template(
        "forms/org.html",
        title="Editing {}".format(org.name),
        form=form,
        action_url=action_url,
    )


@admin.route("/organization/delete/<int:org_id>", methods=["GET"])
@auth_required
@admin_required
def delete_organization(org_id):
    org = db.session.get(Organization, org_id)
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
    pth = db.session.get(ASPath, path_id)
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
    pth = db.session.get(ASPath, path_id)
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
    action = db.session.get(Action, action_id)
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
    action = db.session.get(Action, action_id)
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
    community = db.session.get(Community, community_id)
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
    community = db.session.get(Community, community_id)
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


@admin.route("/set-org-if-zero", methods=["GET"])
@auth_required
@admin_required
def update_set_org():
    # Define the raw SQL update statement
    update_statement = update_statement = text(
        """
        UPDATE organization 
        SET limit_flowspec4 = 0, limit_flowspec6 = 0, limit_rtbh = 0 
        WHERE limit_flowspec4 IS NULL OR limit_flowspec6 IS NULL OR limit_rtbh IS NULL;
    """
    )
    try:
        # Execute the update query
        db.session.execute(update_statement)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating organizations: {e}", "alert-danger")

    # Get all flowspec records where org_id is NULL (if this is needed)
    models = [Flowspec4, Flowspec6, RTBH, ApiKey, MachineApiKey]
    user_with_multiple_orgs = {}
    for model in models:
        data_records = model.query.filter(model.org_id == 0).all()
        # Loop through each flowspec record and update org_id based on the user's organization
        updated = 0
        for row in data_records:
            orgs = row.user.organization.all()
            if len(orgs) == 1:
                user_org = orgs[0]
                if user_org:
                    row.org_id = user_org.id
                    updated += 1
            else:
                user_with_multiple_orgs[row.user.email] = [org.name for org in orgs]
        # Commit the changes
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating {model.__name__}: {e}", "alert-danger")

    return render_template("pages/user_list.html", users=user_with_multiple_orgs, updated=updated)
