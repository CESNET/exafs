from flowspec import translate_sequence as trps

def create_message_from_rule(rule):
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