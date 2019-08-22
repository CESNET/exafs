# flowapp/views/admin.py
from flask import Blueprint, render_template, redirect, flash, request, url_for
from ..forms import UserForm, ActionForm, OrganizationForm, CommunityForm
from ..models import User, Action, Organization, Role, insert_user, get_existing_action, Community, get_existing_community
from ..auth import auth_required, admin_required
from flowapp import db

admin = Blueprint('admin', __name__, template_folder='templates')


@admin.route('/user', methods=['GET', 'POST'])
@auth_required
@admin_required
def user():
    form = UserForm(request.form)
    form.role_ids.choices = [(g.id, g.name)
                             for g in db.session.query(Role).order_by('name')]
    form.org_ids.choices = [(g.id, g.name)
                            for g in db.session.query(Organization).order_by('name')]

    if request.method == 'POST' and form.validate():
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
                org_ids=form.org_ids.data)
            flash('User saved')
            return redirect(url_for('admin.users'))
        else:
            flash(u'User {} already exists'.format(
                form.email.data), 'alert-danger')

    action_url = url_for('admin.user')
    return render_template('forms/simple_form.j2', title="Add new user to Flowspec", form=form, action_url=action_url)


@admin.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@auth_required
@admin_required
def edit_user(user_id):
    user = db.session.query(User).get(user_id)
    form = UserForm(request.form, obj=user)
    form.role_ids.choices = [(g.id, g.name)
                             for g in db.session.query(Role).order_by('name')]
    form.org_ids.choices = [(g.id, g.name)
                            for g in db.session.query(Organization).order_by('name')]

    if request.method == 'POST' and form.validate():
        user.update(form)
        return redirect(url_for('admin.users'))

    form.role_ids.data = [role.id for role in user.role]
    form.org_ids.data = [org.id for org in user.organization]
    action_url = url_for('admin.edit_user', user_id=user_id)

    return render_template('forms/simple_form.j2', title=u"Editing {}".format(user.email), form=form,
                           action_url=action_url)


@admin.route('/user/delete/<int:user_id>', methods=['GET'])
@auth_required
@admin_required
def delete_user(user_id):
    user = db.session.query(User).get(user_id)
    username = user.email
    db.session.delete(user)
    db.session.commit()
    flash(u'User {} deleted'.format(username), 'alert-success')

    return redirect(url_for('admin.users'))


@admin.route('/users')
@auth_required
@admin_required
def users():
    users = User.query.all()
    return render_template('pages/users.j2', users=users)


@admin.route('/organizations')
@auth_required
@admin_required
def organizations():
    orgs = db.session.query(Organization).all()
    return render_template('pages/orgs.j2', orgs=orgs)


@admin.route('/organization', methods=['GET', 'POST'])
@auth_required
@admin_required
def organization():
    form = OrganizationForm(request.form)

    if request.method == 'POST' and form.validate():
        # test if user is unique
        exist = db.session.query(Organization).filter_by(name=form.name.data).first()
        if not exist:
            org = Organization(name=form.name.data, arange=form.arange.data)
            db.session.add(org)
            db.session.commit()
            flash('Organization saved')
            return redirect(url_for('admin.organizations'))
        else:
            flash(u'Organization {} already exists'.format(
                form.name.data), 'alert-danger')

    action_url = url_for('admin.organization')
    return render_template('forms/simple_form.j2', title="Add new organization to Flowspec", form=form,
                           action_url=action_url)


@admin.route('/organization/edit/<int:org_id>', methods=['GET', 'POST'])
@auth_required
@admin_required
def edit_organization(org_id):
    org = db.session.query(Organization).get(org_id)
    form = OrganizationForm(request.form, obj=org)

    if request.method == 'POST' and form.validate():
        form.populate_obj(org)
        db.session.commit()
        flash('Organization updated')
        return redirect(url_for('admin.organizations'))

    action_url = url_for('admin.edit_organization', org_id=org.id)
    return render_template('forms/simple_form.j2', title=u"Editing {}".format(org.name), form=form,
                           action_url=action_url)


@admin.route('/organization/delete/<int:org_id>', methods=['GET'])
@auth_required
@admin_required
def delete_organization(org_id):
    org = db.session.query(Organization).get(org_id)
    aname = org.name
    db.session.delete(org)
    db.session.commit()
    flash(u'Organization {} deleted'.format(aname), 'alert-success')

    return redirect(url_for('admin.organizations'))


@admin.route('/actions')
@auth_required
@admin_required
def actions():
    actions = db.session.query(Action).all()
    return render_template('pages/actions.j2', actions=actions)


@admin.route('/action', methods=['GET', 'POST'])
@auth_required
@admin_required
def action():
    form = ActionForm(request.form)

    if request.method == 'POST' and form.validate():
        # test if Acttion is unique
        exist = get_existing_action(form.name.data, form.command.data)
        if not exist:
            action = Action(name=form.name.data,
                            command=form.command.data,
                            description=form.description.data,
                            role_id=form.role_id.data)
            db.session.add(action)
            db.session.commit()
            flash('Action saved', 'alert-success')
            return redirect(url_for('admin.actions'))
        else:
            flash(u'Action with name {} or command {} already exists'.format(
                form.name.data, form.command.data), 'alert-danger')

    action_url = url_for('admin.action')
    return render_template('forms/simple_form.j2', title="Add new action to Flowspec", form=form, action_url=action_url)


@admin.route('/action/edit/<int:action_id>', methods=['GET', 'POST'])
@auth_required
@admin_required
def edit_action(action_id):
    action = db.session.query(Action).get(action_id)
    print(action.role_id)
    form = ActionForm(request.form, obj=action)
    if request.method == 'POST' and form.validate():
        form.populate_obj(action)
        db.session.commit()
        flash('Action updated')
        return redirect(url_for('admin.actions'))

    action_url = url_for('admin.edit_action', action_id=action.id)
    return render_template('forms/simple_form.j2', title=u"Editing {}".format(action.name), form=form,
                           action_url=action_url)


@admin.route('/action/delete/<int:action_id>', methods=['GET'])
@auth_required
@admin_required
def delete_action(action_id):
    action = db.session.query(Action).get(action_id)
    aname = action.name
    db.session.delete(action)
    db.session.commit()
    flash(u'Action {} deleted'.format(aname), 'alert-success')

    return redirect(url_for('admin.actions'))


@admin.route('/communities')
@auth_required
@admin_required
def communities():
    communities = db.session.query(Community).all()
    return render_template('pages/communities.j2', communities=communities)


@admin.route('/community', methods=['GET', 'POST'])
@auth_required
@admin_required
def community():
    form = CommunityForm(request.form)

    if request.method == 'POST' and form.validate():
        # test if Coomunity name is unique
        exist = get_existing_community(form.name.data)
        if not exist:
            community = Community(name=form.name.data,
                                  comm=form.comm.data,
                                  larcomm=form.larcomm.data,
                                  extcomm=form.extcomm.data,
                                  description=form.description.data,
                                  role_id=form.role_id.data)
            db.session.add(community)
            db.session.commit()
            flash('Community saved', 'alert-success')
            return redirect(url_for('admin.communities'))
        else:
            flash(u'Community with name {} already exists'.format(
                form.name.data, form.command.data), 'alert-danger')

    community_url = url_for('admin.community')
    return render_template('forms/simple_form.j2', title="Add new community to Flowspec", form=form,
                           community_url=community_url)


@admin.route('/community/edit/<int:community_id>', methods=['GET', 'POST'])
@auth_required
@admin_required
def edit_community(community_id):
    community = db.session.query(Community).get(community_id)
    print(community.role_id)
    form = CommunityForm(request.form, obj=community)
    if request.method == 'POST' and form.validate():
        form.populate_obj(community)
        db.session.commit()
        flash('Community updated')
        return redirect(url_for('admin.communities'))

    community_url = url_for('admin.edit_community', community_id=community.id)
    return render_template('forms/simple_form.j2', title=u"Editing {}".format(community.name), form=form,
                           community_url=community_url)


@admin.route('/community/delete/<int:community_id>', methods=['GET'])
@auth_required
@admin_required
def delete_community(community_id):
    community = db.session.query(Community).get(community_id)
    aname = community.name
    db.session.delete(community)
    db.session.commit()
    flash(u'Community {} deleted'.format(aname), 'alert-success')

    return redirect(url_for('admin.communities'))
