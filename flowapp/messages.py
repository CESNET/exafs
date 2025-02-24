from flowapp.constants import (
    ANNOUNCE,
    WITHDRAW,
    IPV4_DEFMASK,
    IPV6_DEFMASK,
    MAX_PACKET,
    IPV4_PROTOCOL,
    IPV6_NEXT_HEADER,
)
from flowapp.flowspec import translate_sequence as trps
from flask import current_app
from flowapp.models import ASPath
from flowapp import db


def create_ipv4(rule, message_type=ANNOUNCE):
    """
    create ExaBpg text message for IPv4 rule
    @param rule models.Flowspec4
    @return string message
    """
    protocol = ""
    if rule.protocol and rule.protocol != "all":
        protocol = "protocol ={};".format(IPV4_PROTOCOL[rule.protocol])

    flagstring = rule.flags.replace(";", " ") if rule.flags else ""

    flags = "tcp-flags {};".format(flagstring) if rule.flags and rule.protocol == "tcp" else ""

    fragment_string = rule.fragment.replace(";", " ") if rule.fragment else ""
    fragment = "fragment [ {} ];".format(fragment_string) if rule.fragment else ""

    spec = {
        "protocol": protocol,
        "flags": flags,
        "fragment": fragment,
        "mask": IPV4_DEFMASK,
    }

    return create_message(rule, spec, message_type)


def create_ipv6(rule, message_type=ANNOUNCE):
    """
    create ExaBpg text message for IPv6 rule
    @param rule models.Flowspec6
    @return string message
    :param message_type:
    """
    protocol = ""
    if rule.next_header and rule.next_header != "all":
        protocol = "next-header ={};".format(IPV6_NEXT_HEADER[rule.next_header])
    flagstring = rule.flags.replace(";", " ")
    flags = "tcp-flags {};".format(flagstring) if rule.flags and rule.next_header == "tcp" else ""

    spec = {"protocol": protocol, "mask": IPV6_DEFMASK, "flags": flags}

    return create_message(rule, spec, message_type)


def create_rtbh(rule, message_type=ANNOUNCE):
    """
    create RTBH message in ExaBgp text format
    route 10.10.10.1/32 next-hop 192.0.2.1 community 65001:666 no-export
    """
    action = "announce"
    if message_type == WITHDRAW:
        action = "withdraw"

    if rule.ipv4:
        my_4mask = sanitize_mask(rule.ipv4_mask, IPV4_DEFMASK)
        source = "{}".format(rule.ipv4) if rule.ipv4 else ""
        source += "/{}".format(my_4mask) if rule.ipv4 else ""
        nexthop = "192.0.2.1"

    if rule.ipv6:
        my_6mask = sanitize_mask(rule.ipv6_mask, IPV6_DEFMASK)
        source = "{}".format(rule.ipv6) if rule.ipv6 else ""
        source += "/{}".format(my_6mask) if rule.ipv6 else ""
        nexthop = "100::1"

    try:
        if current_app.config["USE_RD"]:
            rd_string = "rd {rd} label {label}".format(
                rd=current_app.config["RD_STRING"], label=current_app.config["RD_LABEL"]
            )
        else:
            rd_string = ""
    except KeyError:
        rd_string = ""

    try:
        if current_app.config["USE_MULTI_NEIGHBOR"] and rule.community.comm:
            if rule.community.comm in current_app.config["MULTI_NEIGHBOR"].keys():
                targets = current_app.config["MULTI_NEIGHBOR"].get(rule.community.comm)
            else:
                targets = current_app.config["MULTI_NEIGHBOR"].get("primary")

            neighbor = prepare_multi_neighbor(targets)
        else:
            neighbor = ""
    except KeyError:
        neighbor = ""

    community_string = "community [{}]".format(rule.community.comm) if rule.community.comm else ""
    large_community_string = "large-community [{}]".format(rule.community.larcomm) if rule.community.larcomm else ""
    extended_community_string = (
        "extended-community [{}]".format(rule.community.extcomm) if rule.community.extcomm else ""
    )

    as_path_string = ""
    if rule.community.as_path:
        match = db.session.query(ASPath).filter(ASPath.prefix == source).first()
        as_path_string = f"as-path [ {match.as_path} ]" if match else ""

    return "{neighbor}{action} route {source} next-hop {nexthop} {as_path} {community} {large_community} {extended_community}{rd_string}".format(
        neighbor=neighbor,
        action=action,
        source=source,
        as_path=as_path_string,
        community=community_string,
        large_community=large_community_string,
        extended_community=extended_community_string,
        nexthop=nexthop,
        rd_string=rd_string,
    )


def create_message(rule, ipv_specific, message_type=ANNOUNCE):
    """
    create text message using format

    tcp-flagy

    flow route { match { source 147.230.17.6/32;protocol =tcp;tcp-flags fin
    syn;destination-port =3128 >=8080&<=8088;} then {rate-limit 10000; } }

    announce flow route source 4.0.0.0/24 destination 127.0.0.0/24 protocol
    [ udp ] source-port [ =53 ] destination-port [ =80 ]
    packet-length [ =777 =1122 ] fragment [ is-fragment dont-fragment ] rate-limit 1024"


    """
    action = "announce"
    if message_type == WITHDRAW:
        action = "withdraw"

    smask = sanitize_mask(rule.source_mask, ipv_specific["mask"])
    source = "source {}".format(rule.source) if rule.source else ""
    source += "/{};".format(smask) if rule.source else ""

    source_port = "source-port {};".format(trps(rule.source_port)) if rule.source_port else ""

    dmask = sanitize_mask(rule.dest_mask, ipv_specific["mask"])
    dest = " destination {}".format(rule.dest) if rule.dest else ""
    dest += "/{};".format(dmask) if rule.dest else ""

    dest_port = "destination-port {};".format(trps(rule.dest_port)) if rule.dest_port else ""

    protocol = ipv_specific.get("protocol", "")
    flags = ipv_specific.get("flags", "")
    fragment = ipv_specific.get("fragment", "")

    packet_len = "packet-length {};".format(trps(rule.packet_len, MAX_PACKET)) if rule.packet_len else ""

    values = [source, source_port, dest, dest_port, protocol, fragment, flags, packet_len]
    match_body = " ".join(v for v in values if v)

    command = "{};".format(rule.action.command)

    try:
        if current_app.config["USE_RD"]:
            rd_string = "route-distinguisher {rd};".format(rd=current_app.config["RD_STRING"])
            rt_string = "extended-community target:{rt};".format(rt=current_app.config["RT_STRING"])
        else:
            rd_string = ""
            rt_string = ""
    except KeyError:
        rd_string = ""
        rt_string = ""

    try:
        if current_app.config["USE_MULTI_NEIGHBOR"]:
            targets = current_app.config["MULTI_NEIGHBOR"].get("primary")
            neighbor = prepare_multi_neighbor(targets)
        else:
            neighbor = ""
    except KeyError:
        neighbor = ""

    message_body = "{neighbor}{action} flow route {{ {rd_string} match {{ {match_body} }} then {{ {command} {rt_string} }} }}".format(
        neighbor=neighbor,
        action=action,
        match_body=match_body,
        command=command,
        rd_string=rd_string,
        rt_string=rt_string,
    )

    return message_body


def sanitize_mask(rule_mask, default_mask=IPV4_DEFMASK):
    """
    Sanitize mask / prefix of rule
    :param default_mask: default mask to return if mask is not in the rule
    :param rule: flowspec rule
    :return: int mask
    """
    if rule_mask is None:
        return default_mask

    if 0 <= rule_mask <= default_mask:
        return rule_mask
    else:
        return default_mask


def prepare_multi_neighbor(targets: list):
    """
    prepare multi neighbor string
    """
    neigbors = [f"neighbor {tgt}" for tgt in targets]
    return ", ".join(neigbors) + " "
