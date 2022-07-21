import requests
from flask import current_app


def send_rule_to_ddos_protector(rule, base_url, api_key, key_header='x-api-key'):
    """
    :param rule: Rule dictionary to send to the DDoS Protector
    :param base_url: URL of the REST API endpoint to send the rule to
    :param api_key: API key for the api
    :param key_header: HTTP header name, where the API key should be included
    :return: Response object or None if app is in testing mode

    :raise: ConnectionError - Given URL was not available
    """
    if not current_app.config['TESTING']:
        result = requests.post(base_url + '/rules/', headers={key_header: api_key}, json=rule)
        return result
    return None


def remove_rule_from_ddos_protector(ddp_rule_id, base_url, api_key, key_header='x-api-key'):
    if not current_app.config['TESTING']:
        result = requests.delete(base_url + '/rules/' + str(ddp_rule_id), headers={key_header: api_key})
        return result
    return None
