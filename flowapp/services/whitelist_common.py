from enum import Enum, auto
from functools import lru_cache
import ipaddress
from typing import List, Tuple
from flowapp import db
from flowapp.constants import RuleOrigin, RuleTypes
from flowapp.models import RTBH, RuleWhitelistCache, Whitelist


def add_rtbh_rule_to_cache(model: RTBH, whitelist_id: int, rule_origin: RuleOrigin = RuleOrigin.USER) -> None:
    """
    Add RTBH rule to whitelist cache
    """
    cache = RuleWhitelistCache(rid=model.id, rtype=RuleTypes.RTBH, whitelist_id=whitelist_id, rorigin=rule_origin)
    db.session.add(cache)
    db.session.commit()


def whitelist_rtbh_rule(model: RTBH, whitelist: Whitelist) -> RTBH:
    """
    Whitelist RTBH rule.
    Set rule state to 4 - whitelisted rule, do not announce later
    Add to whitelist cache
    """
    model.rstate_id = 4
    db.session.commit()
    add_rtbh_rule_to_cache(model, whitelist.id, RuleOrigin.USER)
    return model


class Relation(Enum):
    SUBNET = auto()
    SUPERNET = auto()
    EQUAL = auto()
    DIFFERENT = auto()


@lru_cache(maxsize=1024)
def get_network(address: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    """
    Create and cache an IP network object.

    :param address: IP address or network in string format
    :return: Cached IP network object
    """
    return ipaddress.ip_network(address, strict=False)


def check_whitelist_to_rule_relation(rule: str, whitelist_entry: str) -> Relation:
    """
    Checks if the whitelist network is a subnet or supernet or  exactly the same as the rule network.
    Uses cached network objects for better performance.

    :param rule: The IP address or network to check (e.g., "192.168.1.1" or "192.168.1.0/24")
    :param whitelist_entry: The allowed network to compare against (e.g., "192.168.1.0/24")
    :return: Relation between the two networks
    """
    rule_net = get_network(rule)
    whitelist_net = get_network(whitelist_entry)
    if whitelist_net == rule_net:
        return Relation.EQUAL
    if whitelist_net.supernet_of(rule_net):
        return Relation.SUPERNET
    if whitelist_net.subnet_of(rule_net):
        return Relation.SUBNET
    else:
        return Relation.DIFFERENT


def subtract_network(target: str, whitelist: str) -> List[str]:
    """
    Computes the remaining parts of a network after removing the whitelist subnet.
    Uses cached network objects for better performance.

    :param target: The main network (e.g., "192.168.1.0/24")
    :param whitelist: The subnet to remove (e.g., "192.168.1.128/25")
    :return: A list of remaining subnets as strings
    """
    target_net = get_network(target)
    whitelist_net = get_network(whitelist)

    # Check if the whitelist is actually a subnet
    if check_whitelist_to_rule_relation(target, whitelist) != Relation.SUBNET:
        return [target]  # Return the full network if whitelist isn't a valid subnet

    remaining = []

    # Compute ranges before and after the whitelist
    if whitelist_net.network_address > target_net.network_address:
        # Before the whitelist
        start = target_net.network_address
        end = whitelist_net.network_address - 1
        remaining.extend(ipaddress.summarize_address_range(start, end))

    if whitelist_net.broadcast_address < target_net.broadcast_address:
        # After the whitelist
        start = whitelist_net.broadcast_address + 1
        end = target_net.broadcast_address
        remaining.extend(ipaddress.summarize_address_range(start, end))

    # Convert to string format
    return [str(net) for net in remaining]


def check_rule_against_whitelists(rule: str, whitelists: List[str]) -> List[Tuple]:
    """
    Helper function to check a single rule against multiple whitelist entries.
    Creates a cached rule network object for better performance.
    Reduces list of whitelists, where the Relation is not DIFFERENT

    :param rule: The IP address or network to check
    :param whitelists: List of whitelist networks to check against
    :return: tuple of rule, whitelist and relation for each whitelists that is not DIFFERENT
    """
    # Pre-cache the rule network since it will be used multiple times
    get_network(rule)
    items = []
    for whitelist in whitelists:
        rel = check_whitelist_to_rule_relation(rule, whitelist)
        if rel != Relation.DIFFERENT:
            items.append((rule, whitelist, rel))
    return items


def check_whitelist_against_rules(rules: List[str], whitelist: str) -> List[Tuple]:
    """
    Helper function to check if any whitelist entry is a subnet of the rule.
    Creates a cached rule network object for better performance.
    Reduces list of rules, where the Relation is not DIFFERENT

    :param rule: The IP address or network to check against
    :param whitelists: List of whitelist networks to check
    :return: tuple of rule, whitelist and relation for each whitelists that is not DIFFERENT
    """
    # Pre-cache the rule network since it will be used multiple times
    get_network(whitelist)
    items = []
    for rule in rules:
        rel = check_whitelist_to_rule_relation(rule, whitelist)
        if rel != Relation.DIFFERENT:
            items.append((rule, whitelist, rel))
    return items


def clear_network_cache() -> None:
    """
    Clear the network object cache.
    Useful when processing a large number of networks to prevent memory growth.
    """
    get_network.cache_clear()
