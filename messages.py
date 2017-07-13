from flowspec import translate_sequence as trps

def create_text(rule):
    """
    ExaBgp text format
    """
    message = 'announce flow route { match { '
    message += 'source {}'.format(rule.source) if rule.source else ''
    message += '/{};'.format(rule.source_mask if rule.source_mask else 32) if rule.source else ''
    message += ' destination {}'.format(rule.dest) if rule.dest else ''
    message += '/32;'.format(rule.dest_mask if rule.dest_mask else 32) if rule.dest else ''
    message += 'destination-port {};'.format(trps(rule.dest_port)) if rule.dest_port else ''
    message += 'protocol {};'.format(trps(rule.protocol))
    message += '} then {'
    message += '{};'.format(rule.action.command)
    message += ' } }'    
    return message    


def create_ipv4(rule):
    """
    create text message using format

    tcp-flagy, pokud je jich vice, musi byt zadane v hranate zavorce.
    flow route { match { source 147.230.17.6/32;protocol =tcp;tcp-flags [=fin
    =syn];destination-port =3128 >=8080&<=8088;} then {rate-limit 10000; } }

    """
    source = 'source {}'.format(rule.source) if rule.source else ''
    source += '/{};'.format(rule.source_mask if rule.source_mask else 32) if rule.source else ''

    source_port = 'source-port {};'.format(trps(rule.source_port)) if rule.dest_port else ''

    dest = ' destination {}'.format(rule.dest) if rule.dest else ''
    dest += '/{};'.format(rule.dest_mask if rule.dest_mask else 32) if rule.dest else ''

    dest_port = 'destination-port {};'.format(trps(rule.dest_port)) if rule.dest_port else ''

    protocol = 'protocol ={}'.format(rule.protocol) if rule.protocol else ''

    match_body = '{source}{source_port}{dest}{dest_port}{protocol}'.format(
        source=source, 
        source_port=source_port,
        dest=dest,
        dest_port=dest_port,
        protocol=protocol)

    command = '{};'.format(rule.action.command)
    
    message_body = 'announce flow route {{ match {{ {match_body} }} then {{ {command} }} }}'.format(
        match_body=match_body,
        command=command)
    
    return message_body


if __name__ == '__main__':
    print create_text2(None)