from flask import Blueprint, render_template, redirect, flash, request, url_for, session
from os import urandom

from ..forms import ApiKeyForm
from ..models import ApiKey
from ..auth import auth_required

from flowapp import db

api_keys = Blueprint('api_keys', __name__, template_folder='templates')


@api_keys.route('/', methods=['GET'])
@auth_required
def all():
    """
    Show user api keys
    :return: page with keys
    """
    keys = db.session.query(ApiKey).filter_by(user_id=session['user_id']).all()

    return render_template('pages/api_key.j2', keys=keys)


@api_keys.route('/add', methods=['GET', 'POST'])
@auth_required
def add():
    """
    Add new ApiKey
    :return: form or redirect to list of keys
    """
    generated = urandom(24).encode('hex')
    form = ApiKeyForm(request.form, key=generated)

    if request.method == 'POST' and form.validate():
        model = ApiKey(
            machine=form.machine.data,
            key=form.key.data,
            user_id=session['user_id']
        )

        db.session.add(model)
        db.session.commit()
        flash(u'NewKey saved', 'alert-success')

        return redirect(url_for('api_keys.all'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                print(u"Error in the %s field - %s" % (
                    getattr(form, field).label.text,
                    error
                ))

    return render_template('forms/api_key.j2', form=form, generated_key=generated)


@api_keys.route('/delete/<int:key_id>', methods=['GET'])
@auth_required
def delete(key_id):
    """
    Delete api_key and machine
    :param key_id: integer
    """

    model = db.session.query(ApiKey).get(key_id)
    if model.user_id == session['user_id'] or 3 in session['user_role_ids']:
        # delete from db
        db.session.delete(model)
        db.session.commit()
        flash(u'Key deleted', 'alert-success')
    else:
        flash(u"You can't delete this key!", 'alert-danger')

    return redirect(url_for('api_keys.all'))
