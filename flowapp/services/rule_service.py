# flowapp/services/rule_service.py
"""
Service module for rule operations.

This module provides business logic functions for creating, updating,
and managing flow rules, separating these concerns from HTTP handling.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Union

from flask import current_app

from flowapp import db, messages
from flowapp.constants import WITHDRAW, RuleOrigin, RuleTypes, ANNOUNCE
from flowapp.models import (
    get_ipv4_model_if_exists,
    get_ipv6_model_if_exists,
    get_rtbh_model_if_exists,
    Flowspec4,
    Flowspec6,
    RTBH,
    Whitelist,
)
from flowapp.models.rules.whitelist import RuleWhitelistCache
from flowapp.models.utils import check_global_rule_limit, check_rule_limit
from flowapp.output import ROUTE_MODELS, Route, announce_route, log_route, RouteSources, log_withdraw
from flowapp.services.base import announce_rtbh_route
from flowapp.services.whitelist_common import (
    Relation,
    add_rtbh_rule_to_cache,
    create_rtbh_from_whitelist_parts,
    subtract_network,
    whitelist_rtbh_rule,
    check_rule_against_whitelists,
)
from flowapp.services.whitelist_service import create_or_update_whitelist
from flowapp.utils import round_to_ten_minutes, get_state_by_time, quote_to_ent


def reactivate_rule(
    rule_type: RuleTypes,
    rule_id: int,
    expires: datetime,
    comment: str,
    user_id: int,
    org_id: int,
    user_email: str,
    org_name: str,
) -> Tuple[Union[RTBH, Flowspec4, Flowspec6], List[str]]:
    """
    Reactivate a rule by setting a new expiration time.

    Args:
        rule_type: Type of rule (RTBH, IPv4, IPv6)
        rule_id: ID of the rule to reactivate
        expires: New expiration datetime
        comment: Updated comment
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging

    Returns:
        Tuple containing (rule_model, messages)
    """
    model_name = {RuleTypes.RTBH: RTBH, RuleTypes.IPv4: Flowspec4, RuleTypes.IPv6: Flowspec6}[rule_type]

    model = db.session.get(model_name, rule_id)
    if not model:
        return None, ["Rule not found"]

    flashes = []

    # Check if rule will be reactivated
    state = get_state_by_time(expires)

    # Check global limit
    if state == 1 and check_global_rule_limit(rule_type.value):
        return model, ["global_limit_reached"]

    # Check org limit
    if state == 1 and check_rule_limit(org_id, rule_type=rule_type.value):
        return model, ["limit_reached"]

    # Set new expiration date
    model.expires = expires
    # Set again the active state, if the rule is not whitelisted RTBH
    if rule_type == RuleTypes.RTBH:
        model = check_rtbh_whitelisted(model, user_id, flashes, f"{user_email} / {org_name}")
    else:
        model.rstate_id = state

    model.comment = comment
    db.session.commit()

    route_model = ROUTE_MODELS[rule_type.value]

    if model.rstate_id == 1:
        flashes.append("Rule successfully updated, state set to active.")
        # Announce route
        command = route_model(model, ANNOUNCE)
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
            rule_type,
            f"{user_email} / {org_name}",
        )
    else:
        # Withdraw route
        command = route_model(model, WITHDRAW)
        route = Route(
            author=f"{user_email} / {org_name}",
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)
        # Log changes
        log_withdraw(
            user_id,
            route.command,
            rule_type,
            model.id,
            f"{user_email} / {org_name}",
        )
        if model.rstate_id == 4:
            flashes.append("Rule successfully updated, state set to whitelisted.")
        else:
            flashes.append("Rule successfully updated, state set to inactive.")

    return model, flashes


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
        model.rstate_id = get_state_by_time(form_data["expires"])
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
    model = check_rtbh_whitelisted(model, user_id, flashes, author)

    announce_rtbh_route(model, author=author)
    # Log changes
    log_route(user_id, model, RuleTypes.RTBH, author)

    return model, flashes


def check_rtbh_whitelisted(model: RTBH, user_id: int, flashes: List[str], author: str) -> None:
    # Check if rule is whitelisted
    allowed_communities = current_app.config["ALLOWED_COMMUNITIES"]
    if model.community_id in allowed_communities:
        # get all not expired whitelists
        whitelists = db.session.query(Whitelist).filter(Whitelist.expires > datetime.now()).all()
        wl_cache = map_whitelists_to_strings(whitelists)
        results = check_rule_against_whitelists(str(model), wl_cache.keys())
        # check rule against whitelists
        model = evaluate_rtbh_against_whitelists_check_results(user_id, model, flashes, author, wl_cache, results)
    return model


def evaluate_rtbh_against_whitelists_check_results(
    user_id: int,
    model: RTBH,
    flashes: List[str],
    author: str,
    wl_cache: Dict[str, Whitelist],
    results: List[Tuple[str, str, Relation]],
) -> RTBH:
    """
    Evaluate RTBH rule against whitelist check results.
    Process all results for cases where rule is whitelisted by several whitelists.
    """
    for rule, whitelist_key, relation in results:
        if relation == Relation.EQUAL:
            model = whitelist_rtbh_rule(model, wl_cache[whitelist_key])
            msg = f"RTBH Rule {model.id} {model} is equal to active whitelist {whitelist_key}. Rule is whitelisted."
            flashes.append(msg)
            current_app.logger.info(msg)
        elif relation == Relation.SUBNET:
            parts = subtract_network(target=str(model), whitelist=whitelist_key)
            wl_id = wl_cache[whitelist_key].id
            msg = f"RTBH Rule {model.id} {model} is supernet of active whitelist {whitelist_key}. Rule is whitelisted, {len(parts)} subnet rules created."
            flashes.append(msg)
            current_app.logger.info(msg)
            for network in parts:
                new_rule = create_rtbh_from_whitelist_parts(model, wl_id, whitelist_key, network, author, user_id)
                msg = f"Created RTBH rule {new_rule.id} {new_rule} for {network} parted by whitelist {whitelist_key}"
                flashes.append(msg)
                current_app.logger.info(msg)
            model.rstate_id = 4
            add_rtbh_rule_to_cache(model, wl_id, RuleOrigin.USER)
            db.session.commit()
        elif relation == Relation.SUPERNET:
            model = whitelist_rtbh_rule(model, wl_cache[whitelist_key])
            msg = f"RTBH Rule {model.id} {model} is subnet of active whitelist {whitelist_key}. Rule is whitelisted."
            current_app.logger.info(msg)
            flashes.append(msg)
    return model


def map_whitelists_to_strings(whitelists: List[Whitelist]) -> Dict[str, Whitelist]:
    return {str(w): w for w in whitelists}


def delete_rule(
    rule_type: RuleTypes, rule_id: int, user_id: int, user_email: str, org_name: str, allowed_rule_ids: List[int] = None
) -> Tuple[bool, str]:
    """
    Delete a rule with the given id and type.

    Args:
        rule_type: Type of rule (RTBH, IPv4, IPv6)
        rule_id: ID of the rule to delete
        user_id: Current user ID
        user_email: User email for logging
        org_name: Organization name for logging
        allowed_rule_ids: List of rule IDs the user is allowed to delete, None means no restriction

    Returns:
        Tuple containing (success, message)
    """
    model_class = {RuleTypes.RTBH: RTBH, RuleTypes.IPv4: Flowspec4, RuleTypes.IPv6: Flowspec6}[rule_type]

    route_model = ROUTE_MODELS[rule_type.value]

    model = db.session.get(model_class, rule_id)
    if not model:
        return False, "Rule not found"

    # Check permission if allowed_rule_ids is provided
    if allowed_rule_ids is not None and model.id not in allowed_rule_ids:
        return False, "You cannot delete this rule"

    # Withdraw route
    command = route_model(model, WITHDRAW)
    route = Route(
        author=f"{user_email} / {org_name}",
        source=RouteSources.UI,
        command=command,
    )
    announce_route(route)

    # Log withdrawal
    log_withdraw(
        user_id,
        route.command,
        rule_type,
        model.id,
        f"{user_email} / {org_name}",
    )

    # Special handling for RTBH rules
    if rule_type == RuleTypes.RTBH:
        current_app.logger.debug(f"Deleting RTBH rule {rule_id} from cache")
        RuleWhitelistCache.delete_by_rule_id(rule_id)

    # Delete from database
    db.session.delete(model)
    db.session.commit()

    return True, "Rule deleted successfully"


def delete_rtbh_and_create_whitelist(
    rule_id: int,
    user_id: int,
    org_id: int,
    user_email: str,
    org_name: str,
    allowed_rule_ids: List[int] = None,
    whitelist_expires: datetime = None,
) -> Tuple[bool, List[str], Union[Whitelist, None]]:
    """
    Delete an RTBH rule and create a whitelist entry from it.

    Args:
        rule_id: ID of the RTBH rule to delete
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging
        allowed_rule_ids: List of rule IDs the user is allowed to delete
        whitelist_expires: Expiration time for the whitelist entry (default: 7 days from now)

    Returns:
        Tuple containing (success, messages, whitelist_model)
    """
    messages = []

    # First get the RTBH rule to extract its data
    model = db.session.get(RTBH, rule_id)
    if not model:
        return False, ["RTBH rule not found"], None

    # Check permission if allowed_rule_ids is provided
    if allowed_rule_ids is not None and model.id not in allowed_rule_ids:
        return False, ["You cannot delete this rule"], None

    # Extract data for whitelist
    if model.ipv4:
        ip = model.ipv4
        mask = model.ipv4_mask
    elif model.ipv6:
        ip = model.ipv6
        mask = model.ipv6_mask
    else:
        return False, ["RTBH rule has no IP address"], None

    # Set default whitelist expiration time if not provided
    if whitelist_expires is None:
        whitelist_expires = datetime.now() + timedelta(days=7)

    # Prepare whitelist data
    # Create base comment
    comment_text = f"Created from RTBH rule {model} {rule_id}"
    # Append the rule's comment only if it exists
    if model.comment:
        comment_text += f": {model.comment}"

    whitelist_data = {
        "ip": ip,
        "mask": mask,
        "expires": whitelist_expires,
        "comment": comment_text,
    }

    # Delete the RTBH rule
    success, delete_message = delete_rule(
        rule_type=RuleTypes.RTBH,
        rule_id=rule_id,
        user_id=user_id,
        user_email=user_email,
        org_name=org_name,
        allowed_rule_ids=allowed_rule_ids,
    )

    if not success:
        return False, [delete_message], None

    messages.append(delete_message)

    # Create the whitelist entry
    try:
        whitelist_model, whitelist_messages = create_or_update_whitelist(
            form_data=whitelist_data, user_id=user_id, org_id=org_id, user_email=user_email, org_name=org_name
        )
        messages.extend(whitelist_messages)
        return True, messages, whitelist_model
    except Exception as e:
        current_app.logger.exception(f"Error creating whitelist entry: {e}")
        messages.append(f"Rule deleted but failed to create whitelist: {str(e)}")
        return False, messages, None


def delete_expired_rules() -> Dict[str, int]:
    """
    Delete all expired rules older than EXPIRATION_THRESHOLD days.
    Only deletes rules in withdrawn or deleted state.

    Returns:
        Dictionary with deletion counts per rule type
    """
    current_time = datetime.now()
    expiration_threshold = current_app.config.get("EXPIRATION_THRESHOLD", 30)
    deletion_date = current_time - timedelta(days=expiration_threshold)

    deletion_counts = {"rtbh": 0, "ipv4": 0, "ipv6": 0, "total": 0}

    model_map = {
        "rtbh": (RTBH, RuleTypes.RTBH),
        "ipv4": (Flowspec4, RuleTypes.IPv4),
        "ipv6": (Flowspec6, RuleTypes.IPv6),
    }

    for rule_type, (model_class, rule_enum) in model_map.items():
        # Get IDs of rules to delete
        expired_rule_ids = [
            r.id
            for r in db.session.query(model_class.id)
            .filter(
                model_class.expires < deletion_date, model_class.rstate_id.in_([2, 3])  # withdrawn or deleted state
            )
            .all()
        ]

        if not expired_rule_ids:
            current_app.logger.info(f"No expired {model_class.__name__} rules to delete")
            continue

        # Clean up whitelist cache first
        cache_deleted = 0
        for rule_id in expired_rule_ids:
            cache_deleted += RuleWhitelistCache.delete_by_rule_id(rule_id)

        if cache_deleted:
            current_app.logger.info(
                f"Deleted {cache_deleted} cache entries for {len(expired_rule_ids)} {model_class.__name__} rules"
            )

        # Bulk delete the rules
        deleted = (
            db.session.query(model_class).filter(model_class.id.in_(expired_rule_ids)).delete(synchronize_session=False)
        )

        deletion_counts[rule_type] = deleted
        deletion_counts["total"] += deleted

        current_app.logger.info(
            f"Deleted {deleted} expired {model_class.__name__} rules " f"(older than {expiration_threshold} days)"
        )

    # Commit all deletions at once
    if deletion_counts["total"] > 0:
        try:
            db.session.commit()
            current_app.logger.info(
                f"Successfully deleted {deletion_counts['total']} expired rules: "
                f"RTBH={deletion_counts['rtbh']}, "
                f"IPv4={deletion_counts['ipv4']}, "
                f"IPv6={deletion_counts['ipv6']}"
            )
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error committing rule deletions: {e}")
            raise
    else:
        current_app.logger.info("No expired rules found to delete")

    return deletion_counts
