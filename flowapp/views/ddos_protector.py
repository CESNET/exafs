import json

import requests
from flask import Blueprint, flash, redirect, render_template, request, url_for

from flowapp.auth import admin_required, auth_required, user_or_admin_required
from flowapp.forms import DDPDeviceForm
from flowapp.models import (
    DDPRulePreset,
    format_preset,
    DDPRuleExtras,
    DDPDevice,
    get_ddp_extras_model_if_exists, )
from flowapp import db
from flowapp.ddp import send_rule_to_ddos_protector

ddos_protector = Blueprint("ddos-protector", __name__, template_folder="templates")


@ddos_protector.route("/presets", methods=["GET"])
@auth_required
@user_or_admin_required
def presets():
    data = DDPRulePreset.query.all()
    preset_list = []
    for d in data:
        preset_list.append(format_preset(d))
    return render_template("pages/ddp_presets.j2", presets=preset_list)


@ddos_protector.route(
    "/new-preset", methods=["GET", "POST"], defaults={"preset_id": None}
)
@ddos_protector.route("/edit-preset/<preset_id>", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def edit_preset(preset_id):
    preset = None
    if preset_id is not None:
        # Load preset from database
        preset = db.session.get(DDPRulePreset, preset_id)
    return render_template(
        "forms/ddp_preset_form.j2", preset=format_preset(preset), new=preset is None
    )


@ddos_protector.route("/duplicate-preset/<preset_id>", methods=["GET", "POST"])
@auth_required
@user_or_admin_required
def duplicate_preset(preset_id):
    # Load preset from database
    preset = db.session.get(DDPRulePreset, preset_id)
    if not preset:
        flash("Preset not found", "alert-danger")
        return redirect(url_for("ddos-protector.presets"))
    name = getattr(preset, "name")
    setattr(preset, "name", name + " - copy")
    return render_template(
        "forms/ddp_preset_form.j2", preset=format_preset(preset), new=True
    )


@ddos_protector.route("/new-preset-callback", methods=["POST"])
@ddos_protector.route("/edit-preset-callback/<preset_id>", methods=["POST"])
@auth_required
@user_or_admin_required
def preset_form_callback(preset_id=None):
    keys = list(request.form.keys())
    values = list(request.form.values())
    data = {}
    for i in range(len(keys)):
        data[keys[i]] = values[i]

    del data["csrf_token"]
    model = DDPRulePreset(**data)
    if preset_id is None:
        db.session.add(model)
        db.session.commit()
        flash("Preset successfully added", "alert-success")
    else:
        model = db.session.query(DDPRulePreset).get(preset_id)
        model_dict = model.__dict__.copy()
        del model_dict["_sa_instance_state"]
        del model_dict["id"]
        for key in model_dict:
            if key in data:
                setattr(model, key, data[key])
            else:
                setattr(model, key, None)
        db.session.commit()
        flash("Preset successfully updated", "alert-success")
    return "saved"


@ddos_protector.route("/delete-preset/<int:preset_id>", methods=["GET"])
@auth_required
@admin_required
def delete_ddp_preset(preset_id):
    model = db.session.get(DDPRulePreset, preset_id)
    db.session.delete(model)
    db.session.commit()
    flash("Preset deleted", "alert-success")
    return redirect(url_for("ddos-protector.presets"))


@ddos_protector.route("/devices", methods=["GET"])
@auth_required
@user_or_admin_required
def devices():
    data = DDPDevice.query.all()
    return render_template("pages/ddp_devices.j2", devices=data)


@ddos_protector.route(
    "/new-device", methods=["GET", "POST"], defaults={"device_id": None}
)
@ddos_protector.route("/edit-device/<device_id>", methods=["GET", "POST"])
@auth_required
@admin_required
def edit_devices(device_id):
    device = None
    if device_id is not None:
        # Load preset from database
        device = db.session.get(DDPDevice, device_id)
        form = DDPDeviceForm(request.form, obj=device)
        form.populate_obj(device)
    else:
        form = DDPDeviceForm(request.form)

    if request.method == "POST" and form.validate():
        url = form.url.data
        if url[-1] == '/':
            url = url[:-1]
        if device_id is not None:
            device.url = url
            device.key = form.key.data
            device.redirect_command = form.redirect_command.data
            device.active = form.active.data
            device.key_header = form.key_header.data
            device.name = form.name.data
            db.session.commit()
            flash("Device edited", "alert-success")
        else:
            device = DDPDevice(
                url=url,
                key=form.key.data,
                redirect_command=form.redirect_command.data,
                active=form.active.data,
                key_header=form.key_header.data,
                name=form.name.data,
            )
            db.session.add(device)
            db.session.commit()
            flash("Device saved", "alert-success")
        return redirect(url_for("ddos-protector.devices"))

    action_url = url_for("ddos-protector.edit_devices", device_id=device_id)
    return render_template(
        "forms/simple_form.j2",
        title="Add new DDoS Protector device",
        form=form,
        action_url=action_url,
    )


@ddos_protector.route("/delete-device/<int:device_id>", methods=["GET"])
@auth_required
@admin_required
def delete_ddp_device(device_id):
    model = db.session.get(DDPDevice, device_id)
    db.session.delete(model)
    db.session.commit()
    flash("Device deleted", "alert-success")
    return redirect(url_for("ddos-protector.devices"))


def get_ddp_data_from_preset_form(form_data: dict):
    ddp_keys = [
        "ddp_threshold_bps",
        "ddp_threshold_pps",
        "ddp_vlan",
        "ddp_protocol",
        "ddp_threshold_syn_soft",
        "ddp_threshold_syn_hard",
        "ddp_fragmentation",
        "ddp_packet_lengths",
        "ddp_limit_bps",
        "ddp_limit_pps",
        "ddp_tcp_flags",
        "ddp_validity_timeout",
        "ddp_algorithm_type",
        "ddp_table_exponent",
    ]
    result = {}
    for key, value in form_data.items():
        if value is None:
            continue
        if key in ddp_keys:
            # Remove 'ddp_' from the key
            result[key[4:]] = value
    return result


def create_ddp_rule_from_preset_form(
    preset_id, user_modifications: dict, form_data: dict
):
    preset = db.session.get(DDPRulePreset, preset_id)
    rule = preset.__dict__.copy()
    del rule["_sa_instance_state"]
    for key, value in user_modifications.items():
        if key in rule["editable"] and value is not None:
            rule[key] = value
    if form_data["source"] is not None and form_data["source"] != "":
        rule["ip_src"] = [
            create_addr_from_ip_and_mask(form_data["source"], form_data["source_mask"])
        ]
    if form_data["dest"] is not None and form_data["dest"] != "":
        rule["ip_dst"] = [
            create_addr_from_ip_and_mask(form_data["dest"], form_data["dest_mask"])
        ]
    if form_data["source_port"] is not None and form_data["source_port"] != "":
        try:
            rule["port_src"] = parse_ports_for_ddp(form_data["source_port"])
        except ValueError:
            # Should never happen, form validation will not let invalid data pass here
            pass
    if "dest_port" in form_data and form_data["dest_port"] is not None and form_data["dest_port"] != "":
        try:
            rule["port_dst"] = parse_ports_for_ddp(form_data["dest_port"])
        except ValueError:
            # Should never happen, form validation will not let invalid data pass here
            pass
    if "protocol" in rule:
        if "," in rule["protocol"]:
            rule["protocol"] = [f.upper() for f in rule["protocol"].split(",") if f != ""]
    elif "protocol" in form_data and form_data["protocol"] is not None:
        if form_data["protocol"].upper() != "ALL":
            # In DDoS Protector, empty protocol means all
            rule["protocol"] = [form_data["protocol"].upper()]
    if "tcp_flags" in rule and rule["tcp_flags"] is not None and rule["tcp_flags"] != "":
        rule["tcp_flags"] = parse_ddp_tcp_flags(rule["tcp_flags"])
    rule["enabled"] = True
    rule["description"] = 'Generated using ExaFS from the "' + preset.name + '" preset.'
    del rule["editable"]
    if "name" in rule:
        del rule["name"]
    if "id" in rule:
        del rule["id"]
    for key, value in preset.__dict__.items():
        # Filter and amplification rules can specify protocol different from the rule
        if value is None and key != "protocol":
            del rule[key]
    return rule


def create_addr_from_ip_and_mask(ip, mask):
    if mask is not None:
        return ip + "/" + str(mask)
    else:
        return ip


def parse_ports_for_ddp(ports):
    if ports is None:
        return []
    data = []
    input = ports.split(";")
    for i in input:
        if i == "":
            continue
        if i[:2] == "<=":
            d = i[2:]
            if d.isnumeric():
                data.append([0, int(d)])
            else:
                raise ValueError("Invalid port format")
        elif i[:2] == ">=":
            d = i[2:]
            if d.isnumeric():
                data.append([int(d), 65535])
            else:
                raise ValueError("Invalid port format")
        elif i[0] == ">":
            d = i[1:]
            if d.isnumeric():
                data.append([int(d) + 1, 65535])
            else:
                raise ValueError("Invalid port format")
        elif i[0] == "<":
            d = i[1:]
            if d.isnumeric():
                data.append([0, int(d) - 1])
            else:
                raise ValueError("Invalid port format")
        elif "-" in i:
            d = i.split("-")
            if d[0].isnumeric() and d[1].isnumeric() and len(d) == 2:
                data.append([int(d[0]), int(d[1])])
            else:
                raise ValueError("Invalid port format")
        else:
            if i.isnumeric():
                data.append([int(i), int(i)])
            else:
                raise ValueError("Invalid port format")
    return data


def parse_ddp_tcp_flags(val):
    """Check whether the parsed argument is a valid list of TCP flags.
    If it is, transform the values from a string into an internal
    integer representation.

    Parameters
    ----------
    val: str
        Raw argument value provided by the parser.

    Return
    ------
    tuple(int, int)
        TCP flags in the database form - an 8 bit mask and 8 bits of flags.

    Raises
    ------
    ValueError
        If the TCP flags are incorrectly formatted.
    """
    if val is None:
        return None

    for char in val:
        if char not in "CEUAPRSF!":
            raise ValueError(f"Invalid TCP flag {char}")
        if char != "!" and val.count(char) > 1:
            raise ValueError("TCP flags duplicates are not allowed")
    values = 0
    mask = 0
    neg_flag = False
    for char in val:
        flag_mask = 0
        if char == "!":
            if neg_flag:
                raise ValueError("Two successive '!' are not allowed")
            neg_flag = True
            continue
        elif char == "C":
            flag_mask |= 0x80
        elif char == "E":
            flag_mask |= 0x40
        elif char == "U":
            flag_mask |= 0x20
        elif char == "A":
            flag_mask |= 0x10
        elif char == "P":
            flag_mask |= 0x08
        elif char == "R":
            flag_mask |= 0x04
        elif char == "S":
            flag_mask |= 0x02
        elif char == "F":
            flag_mask |= 0x01

        mask |= flag_mask
        if not neg_flag:
            values |= flag_mask
        neg_flag = False

    return [[values, mask]]


def handle_ddp_preset_form(form):
    model_valid = True
    extra_opts = {"preset": form.preset.data}
    mods = get_ddp_data_from_preset_form(form.data)
    extra_opts["preset_modifications"] = mods
    rule = create_ddp_rule_from_preset_form(form.preset.data, mods, form.data)
    print(json.dumps(rule))
    if "ip_dst" not in rule:
        form.dest.errors.append("Destination IP is required with DDoS Protector rules")
        model_valid = False
    if (rule["rule_type"] == "syn_drop" or rule["rule_type"] == "tcp_authenticator")\
            and ("protocol" not in rule or rule["protocol"] != ["TCP"]):
        form.protocol.errors.append(
            "Selected mitigation strategy requires the protocol to be TCP"
        )
        model_valid = False
    if model_valid:
        device = get_available_ddos_protector_device()
        try:
            response = send_rule_to_ddos_protector(
                rule, device.url, device.key, device.key_header
            )
            if response.status_code == 201:
                flash(
                    "DDoS Protector configuration added successfully.", "alert-success"
                )
                new_rule = response.json()
                ddp_model = DDPRuleExtras(
                    preset_id=form.preset.data,
                    ddp_rule_id=new_rule["id"],
                    modifications=json.dumps(mods),
                    device_id=device.id,
                )
                db.session.add(ddp_model)
                db.session.commit()
                return ddp_model, True
            else:
                if response.status_code == 422:
                    flash(
                        "Could not save DDoS Protector rule: invalid rule format",
                        "alert-danger",
                    )
                    print("Invalid format response from DDoS Protector: ")
                    print(json.dumps(response.json()))
                else:
                    flash(
                        "Could not save DDoS Protector rule:"
                        + json.dumps(response.json()),
                        "alert-danger",
                    )
                form.action.errors.append("DDoS Protector rejected the rule")
                return form, False
        except requests.exceptions.ConnectionError as exc:
            flash("Could not save DDoS Protector rule:" + str(exc), "alert-danger")
            form.action.errors.append("Error sending the rule to DDoS Protector")
            return form, False
    else:
        return form, False


def create_ddp_rule_from_extras(model: DDPRuleExtras, device: DDPDevice, rule_type):
    data = None
    if rule_type == 4:
        data = create_ddp_rule_from_preset_form(model.preset_id, json.loads(model.modifications), model.flowspec4.__dict__)
    elif rule_type == 6:
        data = create_ddp_rule_from_preset_form(model.preset_id, json.loads(model.modifications), model.flowspec6.__dict__)
    if data is not None:
        try:
            response = send_rule_to_ddos_protector(data, device.url, device.key, device.key_header)
            if response.status_code == 201:
                flash(
                    "DDoS Protector configuration added successfully.", "alert-success"
                )
                new_rule = response.json()
                model.device_id = device.id
                model.ddp_rule_id = new_rule["id"]
                db.session.commit()
        except requests.exceptions.ConnectionError as exc:
            flash('Could not reactivate the DDoS Protector rule: ' + str(exc.response), 'alert-danger')


def get_available_ddos_protector_device() -> DDPDevice:
    # Select "the best" device out of available devices, return its REST API and address
    device = db.session.query(DDPDevice).filter(DDPDevice.active).first()
    return device


def create_ddp_extras(flowspec_model_id, model_version, form):
    extras_model = None
    if form.preset.data is not None and form.preset.data != -1:
        if flowspec_model_id != -1:
            if model_version == 4:
                extras_model = get_ddp_extras_model_if_exists(
                    flowspec_model_id,
                    None,
                    form.preset.data,
                    json.dumps(get_ddp_data_from_preset_form(form.data)),
                )
            elif model_version == 6:
                extras_model = get_ddp_extras_model_if_exists(
                    None,
                    flowspec_model_id,
                    form.preset.data,
                    json.dumps(get_ddp_data_from_preset_form(form.data)),
                )
            if extras_model is not None:
                flash(
                    "The same DDoS Protector rule already linked to this Flowspec rule, no new DDoS Protector "
                    "rules added.",
                    "alert-info",
                )
                return extras_model, True
        if extras_model is None:
            data, success = handle_ddp_preset_form(form)
            if success:
                return data, True
            else:
                return data, False


