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
