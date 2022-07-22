import json
from typing import List, Union, Tuple

import requests
from flask import flash

from flowapp import db
from flowapp.ddp_api import send_rule_to_ddos_protector
from flowapp.forms import IPv4Form, IPv6Form
from flowapp.models import DDPDevice, DDPRulePreset, DDPRuleExtras


def get_available_ddos_protector_device() -> DDPDevice:
    """
    Select "the best" device out of available devices, return its REST API and address
    For now, this function only selects the first active DDoS protector in DB
    """
    device = db.session.query(DDPDevice).filter(DDPDevice.active).first()
    return device


def parse_ports_for_ddp(ports: str) -> List[List[int]]:
    """
    Parse port string into DDoS Protector format:
    List of lists, where the internal lists each
    have two numbers - min and max value.
    For example, <=50;52 will become [[0, 50], [52,52]]

    :param ports: Ports in the string rule form format (x;>x;x-y;<x;<=x;>=x)
    :returns: Formatted list of lists of numbers
    """
    if ports is None:
        return []
    data = []
    ports = ports.split(";")
    for p in ports:
        if p == "":
            continue
        if p[:2] == "<=":
            d = p[2:]
            if d.isnumeric():
                data.append([0, int(d)])
            else:
                raise ValueError("Invalid port format")
        elif p[:2] == ">=":
            d = p[2:]
            if d.isnumeric():
                data.append([int(d), 65535])
            else:
                raise ValueError("Invalid port format")
        elif p[0] == ">":
            d = p[1:]
            if d.isnumeric():
                data.append([int(d) + 1, 65535])
            else:
                raise ValueError("Invalid port format")
        elif p[0] == "<":
            d = p[1:]
            if d.isnumeric():
                data.append([0, int(d) - 1])
            else:
                raise ValueError("Invalid port format")
        elif "-" in p:
            d = p.split("-")
            if d[0].isnumeric() and d[1].isnumeric() and len(d) == 2:
                data.append([int(d[0]), int(d[1])])
            else:
                raise ValueError("Invalid port format")
        else:
            if p.isnumeric():
                data.append([int(p), int(p)])
            else:
                raise ValueError("Invalid port format")
    return data


def parse_ddp_tcp_flags(val):
    """Check whether the parsed argument is a valid list of TCP flags.
    If it is, transform the values from a string into an internal
    integer representation.
    Combinations can be created using following values:
    C, E, U, A, P, R, S and F.
    If a letter is negated using ‘!’ a packet is accepted only
    if the corresponding flag is not set.
    Otherwise, a value of a flag does not matter.
    Example for SYN and SYN+ACK packets only: "!C!E!U!P!RS!F", returns [[2, 239]]

    :param val: Raw argument value provided by the parser.
    :returns: TCP flags in the DDoS Protector form - an 8 bit mask and 8 bits of flags.
    :raises ValueError: If the TCP flags are incorrectly formatted.
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


def filter_ddp_data_from_preset_form(form_data: dict) -> dict:
    """
    Filter fields related to DDoS Protector rules from any form.
    Removes the "ddp_" prefix.
    """
    ddp_keys = [
        "ddp_threshold_bps",
        "ddp_threshold_pps",
        "ddp_vlan",
        "ddp_protocol",
        "ddp_bpf",
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


def create_addr_from_ip_and_mask(ip, mask):
    if mask is not None:
        return ip + "/" + str(mask)
    else:
        return ip


def create_ddp_rule_from_preset_form(preset_id, user_modifications: dict, form_data: dict) -> dict:
    """
    Create a DDoS Protector rule based on preset, user's modifications and flowspec IP form data.
    Most of the values are read from the DDoS Protector rule preset.
    Before applying modifications, this function checks whether modified fields are allowed to
    be modified in the preset.

    :param preset_id: ID of the preset to use
    :param user_modifications: Dict of modifications to the preset (should only contain keys
    corresponding to user editable fields in the preset, other keys are skipped)
    :param form_data: Dict of values from the Flowspec IP rule form.
    :returns: DDoS Protector rule as a dict
    """
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
    if "protocol" in rule and rule["protocol"] is not None:
        if "," in rule["protocol"]:
            rule["protocol"] = [f.upper() for f in rule["protocol"].split(",") if f != ""]
    elif "protocol" in form_data and form_data["protocol"] is not None:
        if form_data["protocol"].upper() != "ALL" and rule["rule_type"] == "filter":
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


def create_ddp_rule_from_extras(model: DDPRuleExtras, rule_type: int) -> dict:
    """
    Create a DDoS Protector rule from saved information about the rule.

    :param model:
    :param rule_type: Type of the flowspec rule (4 for IPv4, 6 for IPv6)
    :returns: DDoS Protector rule based on the model as a dict
    """
    data = None
    if rule_type == 4:
        data = create_ddp_rule_from_preset_form(
            model.preset_id,
            json.loads(model.modifications),
            model.flowspec4.__dict__
        )
    elif rule_type == 6:
        data = create_ddp_rule_from_preset_form(
            model.preset_id,
            json.loads(model.modifications),
            model.flowspec6.__dict__
        )
    return data


def reactivate_ddp_rule(model: DDPRuleExtras, rule: dict, device: DDPDevice) -> bool:
    """
    Send a DDoS protector rule to a given DDoS protector device and
    verify the response. Updates the DDPRuleExtras model to include
    the correct ddp_rule_id and device_id.

    :param model: DDPRuleExtras model to update after the rule is created
    :param rule: DDoS Protector rule to send
    :param device: DDoS protector device to send the rule to
    :returns: True if sending the rule was successful, False if error occurred
    """
    if rule is not None:
        try:
            response = send_rule_to_ddos_protector(rule, device.url, device.key, device.key_header)
            if response.status_code == 201:
                flash(
                    "DDoS Protector configuration added successfully.", "alert-success"
                )
                new_rule = response.json()
                model.device_id = device.id
                model.ddp_rule_id = new_rule["id"]
                db.session.commit()
                return True
            else:
                return False
        except requests.exceptions.ConnectionError as exc:
            flash('Could not reactivate the DDoS Protector rule: ' + str(exc.response), 'alert-danger')
            return False


def validate_ip_form_for_ddp_rule(
        form: Union[IPv6Form, IPv4Form],
        rule: dict) -> Tuple[Union[IPv6Form, IPv4Form], bool]:
    """
    Check if IP form is valid from the DDoS Protector point of view.
    Returns edited form with errors included, if errors are found.

    :param form: IP form object to check
    :param rule: DDoS Protector rule to check against
    :returns: Tuple where the first item is the form, the second item is bool
    signifying whether the form was valid (True if it was, False if not)
    """
    if "ip_dst" not in rule:
        form.dest.errors.append("Destination IP is required with DDoS Protector rules")
        return form, False
    if rule["rule_type"] == "syn_drop" or rule["rule_type"] == "tcp_authenticator":
        if isinstance(form, IPv4Form) and (form.protocol.data != "tcp" and form.protocol.data != "all"):
            form.protocol.errors.append(
                "Selected mitigation strategy requires the protocol to be TCP or ALL"
            )
            return form, False
        elif isinstance(form, IPv6Form) and (form.next_header.data != "tcp" and form.next_header.data != "all"):
            form.next_header.errors.append(
                "Selected mitigation strategy requires the protocol to be TCP or ALL"
            )
            return form, False
    return form, True
