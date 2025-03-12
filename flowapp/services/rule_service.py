# flowapp/services/rule_service.py
"""
Service module for rule operations.

This module provides business logic functions for creating, updating,
and managing flow rules, separating these concerns from HTTP handling.
"""

from datetime import datetime
from typing import Dict, List, Tuple

from flowapp import db, messages
from flowapp.constants import RuleOrigin, RuleTypes, ANNOUNCE
from flowapp.models import (
    get_ipv4_model_if_exists,
    get_ipv6_model_if_exists,
    get_rtbh_model_if_exists,
    Flowspec4,
    Flowspec6,
    RTBH,
    Whitelist,
    RuleWhitelistCache,
)
from flowapp.output import Route, announce_route, log_route, RouteSources
from flowapp.services.base import announce_rtbh_route
from flowapp.utils import round_to_ten_minutes, get_state_by_time, quote_to_ent
from .whitelist_service import check_rule_against_whitelists, Relation, subtract_network


def create_or_update_ipv4_rule(
    form_data: Dict, user_id: int, org_id: int, user_email: str, org_name: str
) -> Tuple[Flowspec4, str]:
    """
    Create a new IPv4 rule or update an existing one.

    Args:
        form_data: Validated form data
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging

    Returns:
        Tuple containing (rule_model, message)
    """
    # Check for existing model
    model = get_ipv4_model_if_exists(form_data, 1)

    if model:
        model.expires = round_to_ten_minutes(form_data["expires"])
        flash_message = "Existing IPv4 Rule found. Expiration time was updated to new value."
    else:
        # Create new model
        model = Flowspec4(
            source=form_data["source"],
            source_mask=form_data["source_mask"],
            source_port=form_data["source_port"],
            destination=form_data["dest"],
            destination_mask=form_data["dest_mask"],
            destination_port=form_data["dest_port"],
            protocol=form_data["protocol"],
            flags=";".join(form_data["flags"]),
            packet_len=form_data["packet_len"],
            fragment=";".join(form_data["fragment"]),
            expires=round_to_ten_minutes(form_data["expires"]),
            comment=quote_to_ent(form_data["comment"]),
            action_id=form_data["action"],
            user_id=user_id,
            org_id=org_id,
            rstate_id=get_state_by_time(form_data["expires"]),
        )
        db.session.add(model)
        flash_message = "IPv4 Rule saved"

    db.session.commit()

    # Announce route if model is in active state
    if model.rstate_id == 1:
        command = messages.create_ipv4(model, ANNOUNCE)
        route = Route(
            author=f"{user_email} / {org_name}",
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)

    # Log changes
    log_route(
        user_id,
        model,
        RuleTypes.IPv4,
        f"{user_email} / {org_name}",
    )

    return model, flash_message


def create_or_update_ipv6_rule(
    form_data: Dict, user_id: int, org_id: int, user_email: str, org_name: str
) -> Tuple[Flowspec6, str]:
    """
    Create a new IPv6 rule or update an existing one.

    Args:
        form_data: Validated form data
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging

    Returns:
        Tuple containing (rule_model, message)
    """
    # Check for existing model
    model = get_ipv6_model_if_exists(form_data, 1)

    if model:
        model.expires = round_to_ten_minutes(form_data["expires"])
        flash_message = "Existing IPv6 Rule found. Expiration time was updated to new value."
    else:
        # Create new model
        model = Flowspec6(
            source=form_data["source"],
            source_mask=form_data["source_mask"],
            source_port=form_data["source_port"],
            destination=form_data["dest"],
            destination_mask=form_data["dest_mask"],
            destination_port=form_data["dest_port"],
            next_header=form_data["next_header"],
            flags=";".join(form_data["flags"]),
            packet_len=form_data["packet_len"],
            expires=round_to_ten_minutes(form_data["expires"]),
            comment=quote_to_ent(form_data["comment"]),
            action_id=form_data["action"],
            user_id=user_id,
            org_id=org_id,
            rstate_id=get_state_by_time(form_data["expires"]),
        )
        db.session.add(model)
        flash_message = "IPv6 Rule saved"

    db.session.commit()

    # Announce routes
    if model.rstate_id == 1:
        command = messages.create_ipv6(model, ANNOUNCE)
        route = Route(
            author=f"{user_email} / {org_name}",
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)

    # Log changes
    log_route(
        user_id,
        model,
        RuleTypes.IPv6,
        f"{user_email} / {org_name}",
    )

    return model, flash_message


def create_or_update_rtbh_rule(
    form_data: Dict, user_id: int, org_id: int, user_email: str, org_name: str
) -> Tuple[RTBH, List]:
    """
    Create a new RTBH rule or update an existing one.

    Args:
        form_data: Validated form data
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging

    Returns:
        Tuple containing (rule_model, message)
    """
    # Check for existing model
    model = get_rtbh_model_if_exists(form_data)
    flashes = []
    if model:
        model.expires = round_to_ten_minutes(form_data["expires"])
        flashes.append("Existing RTBH Rule found. Expiration time was updated to new value.")
    else:
        # Create new model
        model = RTBH(
            ipv4=form_data["ipv4"],
            ipv4_mask=form_data["ipv4_mask"],
            ipv6=form_data["ipv6"],
            ipv6_mask=form_data["ipv6_mask"],
            community_id=form_data["community"],
            expires=round_to_ten_minutes(form_data["expires"]),
            comment=quote_to_ent(form_data["comment"]),
            user_id=user_id,
            org_id=org_id,
            rstate_id=get_state_by_time(form_data["expires"]),
        )
        db.session.add(model)
        flashes.append("RTBH Rule saved")

    db.session.commit()

    # rule author for logging and announcing
    author = f"{user_email} / {org_name}"

    # Check if rule is whitelisted
    # get all not expired whitelists
    whitelists = db.session.query(Whitelist).filter(Whitelist.expires > datetime.now()).all()
    wl_cache = {str(w): w for w in whitelists}
    results = check_rule_against_whitelists(str(model), wl_cache.keys())
    # check rule against whitelists, stop search when rule is whitelisted first time
    for rule, whitelist_key, relation in results:
        match relation:
            case Relation.EQUAL:
                model = whitelist_rtbh_rule(model, wl_cache[whitelist_key])
                flashes.append(f" Rule is equal to active whitelist {whitelist_key}. Rule is whitelisted.")
                break
            case Relation.SUBNET:
                # split subnet into parts
                parts = subtract_network(target=str(model), whitelist=whitelist_key)
                wl_id = wl_cache[whitelist_key].id
                flashes.append(
                    f" Rule is supernet of active whitelist {whitelist_key}. Rule is whitelisted, {len(parts)} subnet rules created."
                )
                for network in parts:
                    create_rtbh_from_whitelist_parts(model, wl_id, whitelist_key, network, author, user_id)
                    flashes.append(f"DEBUG: Created RTBH rule for {network}, from whitelist {whitelist_key}")

                model.rstate_id = 4
                add_rtbh_rule_to_cache(model, wl_id, RuleOrigin.USER)
                db.session.commit()
                break
            case Relation.SUPERNET:
                model = whitelist_rtbh_rule(model, wl_cache[whitelist_key])
                flashes.append(f" Rule is subnet of active whitelist {whitelist_key}. Rule is whitelisted.")
                break

    announce_rtbh_route(model, author=author)
    # Log changes
    log_route(user_id, model, RuleTypes.RTBH, author)

    return model, flashes


def create_rtbh_from_whitelist_parts(
    model: RTBH, wl_id: int, whitelist_key: str, network: str, rule_owner: str, user_id: int
) -> None:
    net_ip, net_mask = network.split("/")
    new_model = RTBH(
        ipv4=net_ip,
        ipv4_mask=net_mask,
        ipv6=model.ipv6,
        ipv6_mask=model.ipv6_mask,
        community_id=model.community_id,
        expires=model.expires,
        comment=model.comment,
        user_id=model.user_id,
        org_id=model.org_id,
        rstate_id=1,
    )
    db.session.add(new_model)
    db.session.commit()
    add_rtbh_rule_to_cache(new_model, wl_id, RuleOrigin.WHITELIST)
    announce_rtbh_route(new_model, rule_owner)
    log_route(user_id, model, RuleTypes.RTBH, rule_owner)


def add_rtbh_rule_to_cache(model: RTBH, whitelist_id: int, rule_origin: RuleOrigin = RuleOrigin.USER) -> None:
    # add to cache
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
