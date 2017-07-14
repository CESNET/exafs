from flowspec import translate_sequence as trps
from flowspec import MAX_PORT, MAX_PACKET



def create_ipv4(rule):
    """
    create ExaBpg text message for IPv4 rule
    @param rule models.Flowspec4
    @return string message
    """
    protocol = 'protocol ={};'.format(rule.protocol) if rule.protocol else ''
    return create_message(rule, protocol)



def create_ipv6(rule):
    """
    create ExaBpg text message for IPv6 rule
    @param rule models.Flowspec6
    @return string message
    """
    protocol = 'next-header ={};'.format(rule.next_header) if rule.next_header else ''
    return create_message(rule, protocol)



def create_message(rule, ipv_specicic):
    """
    create text message using format

    tcp-flagy, pokud je jich vice, musi byt zadane v hranate zavorce.
    flow route { match { source 147.230.17.6/32;protocol =tcp;tcp-flags [=fin
    =syn];destination-port =3128 >=8080&<=8088;} then {rate-limit 10000; } }

    announce flow route source 4.0.0.0/24 destination 127.0.0.0/24 protocol 
    [ udp ] source-port [ =53 ] destination-port [ =80 ] 
    packet-length [ =777 =1122 ] fragment [ is-fragment dont-fragment ] rate-limit 1024" 


    """
    source = 'source {}'.format(rule.source) if rule.source else ''
    source += '/{};'.format(rule.source_mask if rule.source_mask else 32) if rule.source else ''

    source_port = 'source-port {};'.format(trps(rule.source_port)) if rule.dest_port else ''

    dest = ' destination {}'.format(rule.dest) if rule.dest else ''
    dest += '/{};'.format(rule.dest_mask if rule.dest_mask else 32) if rule.dest else ''

    dest_port = 'destination-port {};'.format(trps(rule.dest_port)) if rule.dest_port else ''

    protocol = ipv_specicic

    flagstring = rule.flags.replace(";"," =")
    flags = 'tcp-flags [={}];'.format(flagstring) if rule.flags and rule.protocol=='tcp' else ''

    packet_len = 'packet-length [{}];'.format(trps(rule.packet_len, MAX_PACKET)) if rule.packet_len else ''

    match_body = '{source} {source_port} {dest} {dest_port} {protocol} {flags} {packet_len}'.format(
        source=source, 
        source_port=source_port,
        dest=dest,
        dest_port=dest_port,
        protocol=protocol,
        flags=flags,
        packet_len=packet_len)

    command = '{};'.format(rule.action.command)
    
    message_body = 'announce flow route {{ match {{ {match_body} }} then {{ {command} }} }}'.format(
        match_body=match_body,
        command=command)
    
    return message_body




if __name__ == '__main__':
    print create_text2(None)