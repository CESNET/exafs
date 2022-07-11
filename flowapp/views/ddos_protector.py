import requests
from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
from flowapp.auth import (admin_required, auth_required, localhost_only,
                          user_or_admin_required)
from flowapp.models import DDPApiKey, DDPRulePreset, format_preset
from flowapp import db
import copy

ddos_protector = Blueprint('ddos-protector', __name__, template_folder='templates')


@ddos_protector.route('/presets', methods=['GET'])
@auth_required
@user_or_admin_required
def presets():
    data = db.session.query(DDPRulePreset).all()
    presets = []
    for d in data:
        presets.append(format_preset(d))
    return render_template('pages/ddp_presets.j2', presets=presets)


@ddos_protector.route('/new-preset', methods=['GET', 'POST'], defaults={'preset_id': None})
@ddos_protector.route('/edit-preset/<preset_id>', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def edit_preset(preset_id):
    preset = None
    if preset_id is not None:
        # Load preset from database
        preset = db.session.query(DDPRulePreset).get(preset_id)
    return render_template('forms/ddp_preset_form.j2',
                           preset=format_preset(preset),
                           new=preset is None)


@ddos_protector.route('/duplicate-preset/<preset_id>', methods=['GET', 'POST'])
@auth_required
@user_or_admin_required
def duplicate_preset(preset_id):
    # Load preset from database
    preset = db.session.query(DDPRulePreset).get(preset_id)
    if not preset:
        flash(u'Preset not found', 'alert-danger')
        return redirect(url_for('ddos-protector.presets'))
    name = getattr(preset, 'name')
    setattr(preset, 'name', name + ' - copy')
    return render_template('forms/ddp_preset_form.j2', preset=format_preset(preset), new=True)


@ddos_protector.route('/new-preset-callback', methods=['POST'])
@ddos_protector.route('/edit-preset-callback/<preset_id>', methods=['POST'])
@auth_required
@user_or_admin_required
def preset_form_callback(preset_id=None):
    keys = list(request.form.keys())
    values = list(request.form.values())
    data = {}
    for i in range(len(keys)):
        data[keys[i]] = values[i]

    del data['csrf_token']
    model = DDPRulePreset(
        **data
    )
    if preset_id is None:
        db.session.add(model)
        db.session.commit()
        flash(u'Preset successfully added', 'alert-success')
    else:
        model = db.session.query(DDPRulePreset).get(preset_id)
        for key in data:
            setattr(model, key, data[key])
        db.session.commit()
        flash(u'Preset successfully updated', 'alert-success')
    return 'saved'


@ddos_protector.route('/new-ddp-rule', methods=['POST'])
@auth_required
@user_or_admin_required
def new_ddp_rule_callback():
    conns = db.session.query(DDPApiKey).all()
    keys = list(request.form.keys())
    values = list(request.form.values())
    data = {}
    for i in range(len(keys)):
        if not values[i]:
            continue
        data[keys[i]] = values[i]
    del data['csrf_token']
    if 'port_src' in data:
        data['port_src'] = parse_ports_for_ddp(data['port_src'])
    if 'port_dst' in data:
        data['port_dst'] = parse_ports_for_ddp(data['port_dst'])
    if 'protocol' in data:
        data['protocol'] = [data['protocol'].upper()]
    if 'ip_src' in data:
        data['ip_src'] = [data['ip_src']]
    if 'ip_dst' in data:
        data['ip_dst'] = [data['ip_dst']]
    print(data)
    try:
        for c in conns:
            if c.active:
                retval = requests.post(c.url + '/rules/', json=data, headers={'x-api-key': c.key})
                print(retval)
                if retval.status_code != 201:
                    return str(retval.json())
    except Exception as e:
        return str(e)
    return 'saved'


@ddos_protector.route('/delete-preset/<int:preset_id>', methods=['GET'])
@auth_required
@admin_required
def delete_ddp_preset(preset_id):
    model = db.session.query(DDPRulePreset).get(preset_id)
    db.session.delete(model)
    db.session.commit()
    flash(u'Preset deleted', 'alert-success')
    return redirect(url_for('ddos-protector.presets'))


def parse_ports_for_ddp(ports):
    data = []
    input = ports.split(';')
    for i in input:
        if i[:2] == '<=':
            d = i[2:]
            if d.isnumeric():
                data.append([0, int(d)])
            else:
                raise ValueError('Invalid port format')
        elif i[:2] == '>=':
            d = i[2:]
            if d.isnumeric():
                data.append([int(d), 65535])
            else:
                raise ValueError('Invalid port format')
        elif i[0] == '>':
            d = i[1:]
            if d.isnumeric():
                data.append([int(d) + 1, 65535])
            else:
                raise ValueError('Invalid port format')
        elif i[0] == '<':
            d = i[1:]
            if d.isnumeric():
                data.append([0, int(d) - 1])
            else:
                raise ValueError('Invalid port format')
        elif '-' in i:
            d = i.split('-')
            if d[0].isnumeric() and d[1].isnumeric() and len(d) == 2:
                data.append([int(d[0]), int(d[1])])
            else:
                raise ValueError('Invalid port format')
        else:
            if i.isnumeric():
                data.append([int(i), int(i)])
            else:
                raise ValueError('Invalid port format')
    return data

