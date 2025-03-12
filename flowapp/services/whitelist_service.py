# flowapp/services/rule_service.py
"""
Service module for rule operations.

This module provides business logic functions for creating, updating,
and managing flow rules, separating these concerns from HTTP handling.
"""

from typing import Dict, Tuple, List

from flowapp import db
from flowapp.constants import RuleOrigin, RuleTypes
from flowapp.models import Whitelist, RuleWhitelistCache, get_whitelist_model_if_exists
from flowapp.models.rules.flowspec import Flowspec4, Flowspec6
from flowapp.models.rules.rtbh import RTBH
from flowapp.services.base import announce_rtbh_route
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

    if model:
        model.expires = round_to_ten_minutes(form_data["expires"])
        flash_message = "Existing Whitelist found. Expiration time was updated to new value."
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
        flash_message = "Whitelist saved"

    db.session.commit()

    return model, flash_message


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
        for cached_rule in cached_rules:
            rule_model_type = RuleTypes(cached_rule.rtype)
            match rule_model_type:
                case RuleTypes.IPv4:
                    rule_model = db.session.get(Flowspec4, cached_rule.rid)
                case RuleTypes.IPv6:
                    rule_model = db.session.get(Flowspec6, cached_rule.rid)
                case RuleTypes.RTBH:
                    rule_model = db.session.get(RTBH, cached_rule.rid)
            rorigin_type = RuleOrigin(cached_rule.rorigin)
            if rorigin_type == RuleOrigin.WHITELIST:
                flashes.append(f"Deleted rule {rule_model} created by this whitelist")
                db.session.delete(rule_model)
            elif rorigin_type == RuleOrigin.USER:
                flashes.append(f"Set rule {rule_model} back to state 'Active'")
                rule_model.rstate_id = 1  # Set rule state to "Active" again
                author = f"{model.user.email} ({model.user.organization})"
                announce_rtbh_route(rule_model, author)

        flashes.append(f"Deleted cache entries for whitelist {whitelist_id}")
        RuleWhitelistCache.clean_by_whitelist_id(whitelist_id)

        db.session.delete(model)
        db.session.commit()

    return flashes
