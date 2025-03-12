from flowapp import db, messages
from flowapp.constants import ANNOUNCE, RuleOrigin, RuleTypes
from flowapp.models import RTBH, RuleWhitelistCache
from flowapp.output import Route, RouteSources, announce_route


def announce_rtbh_route(model: RTBH, author: str) -> None:
    """
    Announce RTBH route if rule is in active state
    """
    if model.rstate_id == 1:
        command = messages.create_rtbh(model, ANNOUNCE)
        route = Route(
            author=author,
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)


def add_rtbh_rule_to_cache(model: RTBH, whitelist_id: int, rule_origin: RuleOrigin = RuleOrigin.USER) -> None:
    """
    Add RTBH rule to whitelist cache
    """
    cache = RuleWhitelistCache(rid=model.id, rtype=RuleTypes.RTBH, whitelist_id=whitelist_id, rorigin=rule_origin)
    db.session.add(cache)
    db.session.commit()
