# flowapp/services/rule_service.py
"""
Service module for rule operations.

This module provides business logic functions for creating, updating,
and managing flow rules, separating these concerns from HTTP handling.
"""
from flask import current_app
from typing import Dict, Tuple, List

import sqlalchemy

from flowapp import db
from flowapp.constants import RuleOrigin, RuleTypes
from flowapp.models import Whitelist, RuleWhitelistCache, get_whitelist_model_if_exists
from flowapp.models.rules.flowspec import Flowspec4, Flowspec6
from flowapp.models.rules.rtbh import RTBH
from flowapp.services.base import announce_rtbh_route, withdraw_rtbh_route
from flowapp.services.whitelist_common import add_rtbh_rule_to_cache, create_rtbh_from_whitelist_parts
from flowapp.services.whitelist_common import (
    Relation,
    check_whitelist_against_rules,
    subtract_network,
    whitelist_rtbh_rule,
)
from flowapp.utils import round_to_ten_minutes, quote_to_ent


def create_or_update_whitelist(
    form_data: Dict, user_id: int, org_id: int, user_email: str, org_name: str
) -> Tuple[Whitelist, str]:
    """
    Create a new Whitelist rule or update expiration time of an existing one.

    Args:
        form_data: Validated form data
        user_id: Current user ID
        org_id: Current organization ID
        user_email: User email for logging
        org_name: Organization name for logging

    Returns:
        Tuple containing (whitelist_model, message)
    """
    # Check for existing model
    model = get_whitelist_model_if_exists(form_data)
    flashes = []
    if model:
        model.expires = round_to_ten_minutes(form_data["expires"])
        flashes.append("Existing Whitelist found. Expiration time was updated to new value.")
    else:
        # Create new model
        model = Whitelist(
            ip=form_data["ip"],
            mask=form_data["mask"],
            expires=round_to_ten_minutes(form_data["expires"]),
            user_id=user_id,
            org_id=org_id,
            comment=quote_to_ent(form_data["comment"]),
        )
        db.session.add(model)
        flashes.append("Whitelist saved")

    db.session.commit()

    # check RTBH rules against whitelist
    allowed_communities = current_app.config["ALLOWED_COMMUNITIES"]
    # filter out RTBH rules that are not active or whitelisted and not in allowed communities
    all_rtbh_rules = RTBH.query.filter(RTBH.rstate_id.in_([1, 4]), RTBH.community_id.in_(allowed_communities)).all()
    rtbh_rules_map = map_rtbh_rules_to_strings(all_rtbh_rules)
    result = check_whitelist_against_rules(rtbh_rules_map, str(model))
    current_app.logger.info(f"Found {len(result)} matching RTBH rules for whitelist {model}")
    model = evaluate_whitelist_against_rtbh_check_results(model, flashes, rtbh_rules_map, result)

    return model, flashes


def evaluate_whitelist_against_rtbh_check_results(
    whitelist_model: Whitelist,
    flashes: List[str],
    rtbh_rule_cache: Dict[str, Whitelist],
    results: List[Tuple[str, str, Relation]],
) -> Whitelist:

    for rule_key, whitelist_key, relation in results:
        current_app.logger.info(f"whitelist {whitelist_key} is {relation} to Rule {rule_key}")
        if relation == Relation.EQUAL:
            whitelist_rtbh_rule(rtbh_rule_cache[rule_key], whitelist_model)
            withdraw_rtbh_route(rtbh_rule_cache[rule_key])
            msg = "Existing active rule {rule_key} is equal to whitelist {whitelist_key}. Rule is now whitelisted."
            flashes.append(msg)
            current_app.logger.info(msg)
        elif relation == Relation.SUBNET:
            parts = subtract_network(target=rule_key, whitelist=whitelist_key)
            wl_id = whitelist_model.id
            msg = f"Rule {rule_key} is supernet of whitelist {whitelist_key}. Rule is whitelisted, {len(parts)} subnet rules will be created."
            flashes.append(msg)
            current_app.logger.info(msg)
            for network in parts:
                rule_model = rtbh_rule_cache[rule_key]
                create_rtbh_from_whitelist_parts(rule_model, wl_id, whitelist_key, network)
                msg = f"Created RTBH rule from {rule_model.id} {network} parted by whitelist {whitelist_key}."
                flashes.append(msg)
                current_app.logger.info(msg)
            rule_model.rstate_id = 4
            add_rtbh_rule_to_cache(rule_model, wl_id, RuleOrigin.USER)
            db.session.commit()
        elif relation == Relation.SUPERNET:

            whitelist_rtbh_rule(rtbh_rule_cache[rule_key], whitelist_model)
            withdraw_rtbh_route(rtbh_rule_cache[rule_key])
            msg = f"Existing active rule {rule_key} is subnet of whitelist {whitelist_key}. Rule is now whitelisted."
            current_app.logger.info(msg)
            flashes.append(msg)

    return whitelist_model


def map_rtbh_rules_to_strings(all_rtbh_rules: List[RTBH]) -> Dict[str, RTBH]:
    return {str(rule): rule for rule in all_rtbh_rules}


def delete_expired_whitelists() -> List[str]:
    """
    Delete all expired whitelist entries from the database.

    Returns:
        List of messages for the user
    """
    expired_whitelists = Whitelist.query.filter(Whitelist.expires < db.func.now()).all()
    flashes = []
    for model in expired_whitelists:
        flashes.extend(delete_whitelist(model.id))
    return flashes


def delete_whitelist(whitelist_id: int) -> List[str]:
    """
    Delete a whitelist entry from the database.

    Args:
        whitelist_id: The ID of the whitelist to delete
    """
    model = db.session.get(Whitelist, whitelist_id)
    flashes = []
    if model:
        cached_rules = RuleWhitelistCache.get_by_whitelist_id(whitelist_id)
        current_app.logger.info(
            f"Deleting whitelist {whitelist_id} {model}. Found {len(cached_rules)} cached rules to process."
        )
        for cached_rule in cached_rules:
            rule_model_type = RuleTypes(cached_rule.rtype)
            cache_entries_count = RuleWhitelistCache.count_by_rule(cached_rule.rid, rule_model_type)
            if rule_model_type == RuleTypes.IPv4:
                rule_model = db.session.get(Flowspec4, cached_rule.rid)
            elif rule_model_type == RuleTypes.IPv6:
                rule_model = db.session.get(Flowspec6, cached_rule.rid)
            elif rule_model_type == RuleTypes.RTBH:
                rule_model = db.session.get(RTBH, cached_rule.rid)
            rorigin_type = RuleOrigin(cached_rule.rorigin)
            current_app.logger.debug(f"Rule {rule_model} has origin {rorigin_type}")
            if rorigin_type == RuleOrigin.WHITELIST:
                msg = f"Deleted {rule_model_type} rule {rule_model} created by whitelist {model}"
                current_app.logger.info(msg)
                flashes.append(msg)
                try:
                    db.session.delete(rule_model)
                except sqlalchemy.orm.exc.UnmappedInstanceError:
                    current_app.logger.warning(
                        f"RuleWhitelistCache Anomaly! Rule {rule_model} does not exist. Type {rule_model_type} RID {cached_rule.rid} ID {cached_rule.id} Skipping."
                    )

            elif rorigin_type == RuleOrigin.USER and cache_entries_count == 1:
                msg = f"Set rule {rule_model} back to state 'Active'"
                current_app.logger.info(msg)
                flashes.append(msg)
                try:
                    rule_model.rstate_id = 1  # Set rule state to "Active" again
                except AttributeError:
                    current_app.logger.warning(
                        f"RuleWhitelistCache Anomaly! Rule {rule_model} does not exist. Type {rule_model_type} RID {cached_rule.rid} ID {cached_rule.id} Skipping."
                    )
                else:
                    author = f"{model.user.email} ({model.user.organization})"
                    announce_rtbh_route(rule_model, author)

        msg = f"Deleted cache entries for whitelist {whitelist_id} {model}"
        current_app.logger.info(msg)
        flashes.append(msg)
        RuleWhitelistCache.clean_by_whitelist_id(whitelist_id)

        db.session.delete(model)
        db.session.commit()
        msg = f"Deleted whitelist {whitelist_id} {model}"
        flashes.append(msg)
        current_app.logger.info(msg)

    return flashes
