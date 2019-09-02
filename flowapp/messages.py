from flowapp.constants import ANNOUNCE, WITHDRAW, IPV4_DEFMASK, IPV6_DEFMASK, MAX_PACKET, IPV4_PROTOCOL, \
    IPV6_NEXT_HEADER
from flowspec import translate_sequence as trps


def create_ipv4(rule, message_type=ANNOUNCE):
    """
    create ExaBpg text message for IPv4 rule
    @param rule models.Flowspec4
    @return string message
    """
    protocol = 'protocol ={};'.format(IPV4_PROTOCOL[rule.protocol]) if rule.protocol else ''
    flagstring = rule.flags.replace(";", " ")
    flags = 'tcp-flags {};'.format(
        flagstring) if rule.flags and rule.protocol == 'tcp' else ''

    spec = {
        'protocol': protocol,
        'flags': flags,
        'mask': IPV4_DEFMASK
    }

    return create_message(rule, spec, message_type)


def create_ipv6(rule, message_type=ANNOUNCE):
    """
    create ExaBpg text message for IPv6 rule
    @param rule models.Flowspec6
    @return string message
    :param message_type:
    """
    protocol = 'next-header ={};'.format(
        IPV6_NEXT_HEADER[rule.next_header]) if rule.next_header else ''
    flagstring = rule.flags.replace(";", " ")
    flags = 'tcp-flags {};'.format(
        flagstring) if rule.flags and rule.next_header == 'tcp' else ''

    spec = {
        'protocol': protocol,
        'mask': IPV6_DEFMASK,
        'flags': flags
    }

    return create_message(rule, spec, message_type)


def create_rtbh(rule, message_type=ANNOUNCE):
    """
    create RTBH message in ExaBgp text format
    route 10.10.10.1/32 next-hop 192.0.2.1 community 65001:666 no-export
    """
    action = 'announce'
    if message_type == WITHDRAW:
        action = 'withdraw'

    if rule.ipv4:
        if 0 <= rule.ipv4_mask <= IPV4_DEFMASK:
            my_mask = rule.ipv4_mask
        else:
            my_mask = IPV4_DEFMASK

        source = '{}'.format(rule.ipv4) if rule.ipv4 else ''
        source += '/{}'.format(my_mask) if rule.ipv4 else ''
        nexthop = '192.0.2.1'

    if rule.ipv6:
        if 0 <= rule.ipv4_mask <= IPV6_DEFMASK:
            my_mask = rule.ipv4_mask
        else:
            my_mask = IPV6_DEFMASK

        source = '{}'.format(rule.ipv6) if rule.ipv6 else ''
        source += '/{}'.format(my_mask) if rule.ipv6 else ''
        nexthop = '100::1'

    community_string = "community [{}]".format(rule.community.comm) if rule.community.comm else ""
    large_community_string = "large-community [{}]".format(rule.community.larcomm) if rule.community.larcomm else ""
    extended_community_string = "extended-community [{}]".format(rule.community.extcomm) if rule.community.extcomm else ""

    return "{action} route {source} next-hop {nexthop} {community} {large_community} {extended_community}".format(
        action=action,
        source=source,
        community=community_string,
        large_community=large_community_string,
        extended_community=extended_community_string,
        nexthop=nexthop)


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
    action = 'announce'
    if message_type == WITHDRAW:
        action = 'withdraw'

    smask = sanitize_mask(rule.source_mask, ipv_specific['mask'])
    source = 'source {}'.format(rule.source) if rule.source else ''
    source += '/{};'.format(smask) if rule.source else ''

    source_port = 'source-port {};'.format(
        trps(rule.source_port)) if rule.source_port else ''

    dmask = sanitize_mask(rule.dest_mask, ipv_specific['mask'])
    dest = ' destination {}'.format(rule.dest) if rule.dest else ''
    dest += '/{};'.format(dmask) if rule.dest else ''

    dest_port = 'destination-port {};'.format(
        trps(rule.dest_port)) if rule.dest_port else ''

    protocol = ipv_specific['protocol']
    flags = ipv_specific['flags']

    packet_len = 'packet-length {};'.format(
        trps(rule.packet_len, MAX_PACKET)) if rule.packet_len else ''

    match_body = '{source} {source_port} {dest} {dest_port} {protocol} {flags} {packet_len}'.format(
        source=source,
        source_port=source_port,
        dest=dest,
        dest_port=dest_port,
        protocol=protocol,
        flags=flags,
        packet_len=packet_len)

    command = '{};'.format(rule.action.command)

    message_body = '{action} flow route {{ match {{ {match_body} }} then {{ {command} }} }}'.format(
        action=action,
        match_body=match_body,
        command=command)

    return message_body


def sanitize_mask(rule_mask, default_mask =IPV4_DEFMASK):
    """
    Sanitize mask / prefix of rule
    :param default_mask: default mask to return if mask is not in the rule
    :param rule: flowspec rule
    :return: int mask
    """
    if 0 <= rule_mask <= default_mask:
        return rule_mask
    else:
        return default_mask
