import re

NUMBER = re.compile(r'^\d+$', re.IGNORECASE)
RANGE = re.compile(r'^(\d+)-(\d+)$', re.IGNORECASE)
NOTRAN = re.compile(r'^>=(\d+)&<=(\d+)$', re.IGNORECASE)
GREATER = re.compile(r'>[=]?(\d+)$', re.IGNORECASE)
LOWER = re.compile(r'<[=]?(\d+)$', re.IGNORECASE)


def translate_sequence(sequence):
    """
    translate command sequence sepparated by ; to ExaBGP command format
    """
    result = [translate_port_string(item) for item in sequence.split(";") if item]
    return " ".join(result)

def translate_port_string(port_string):
    """
    Translate port string to flowspec port rule
    @param string port_string
    @return string port rule string
    @raises ValueError

    x (integer)  to =x
    x-y  to >=x&<=y
    >=x&<=y to >=x&<=y
    >x to >=x&<=65535
    >=x to >=x&<=65535
    <x to >=0&<=x
    <=x to >=0&<=x
    """
    # simple number
    if NUMBER.match(port_string):
        return "={}".format(port_limit(port_string))
    elif RANGE.match(port_string):
        m = RANGE.match(port_string)
        return ">={}&<={}".format(port_limit(m.group(1)), port_limit(m.group(2)))
    elif NOTRAN.match(port_string):
        return port_string
    elif GREATER.match(port_string):
        m = GREATER.match(port_string)
        return ">={}&<=65535".format(port_limit(m.group(1)))
    elif LOWER.match(port_string):
        m = LOWER.match(port_string)
        return ">=0&<={}".format(port_limit(m.group(1)))
    else:
        raise ValueError("string {} can not be converted".format(port_string))


def port_limit(port):
    """
    test if the port is lower than 65535
    raise exception otherwise
    """
    port = int(port)
    if port > 65535:
        raise ValueError("Invalid port number: {}".format(port))        
    else:
        return port


