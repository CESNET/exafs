from typing import List

from flowapp import db
from flowapp.models import DDPDevice


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
