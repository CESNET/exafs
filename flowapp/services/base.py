from datetime import datetime
from operator import ge, lt
from flowapp import constants, db, messages
from flowapp.constants import ANNOUNCE, WITHDRAW
from flowapp.models import RTBH, Flowspec4, Flowspec6
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


def withdraw_rtbh_route(model: RTBH) -> None:
    """
    Withdraw RTBH route if rule is in whitelist state
    """
    if model.rstate_id == 4:
        command = messages.create_rtbh(model, WITHDRAW)
        route = Route(
            author=model.get_author(),
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)


def announce_all_routes(action=constants.ANNOUNCE):
    """
    get routes from db and send it to ExaBGB api

    @TODO take the request away, use some kind of messaging (maybe celery?)
    :param action: action with routes - announce valid routes or withdraw expired routes
    """
    today = datetime.now()
    comp_func = ge if action == constants.ANNOUNCE else lt

    rules4 = (
        db.session.query(Flowspec4)
        .filter(Flowspec4.rstate_id == 1)
        .filter(comp_func(Flowspec4.expires, today))
        .order_by(Flowspec4.expires.desc())
        .all()
    )
    rules6 = (
        db.session.query(Flowspec6)
        .filter(Flowspec6.rstate_id == 1)
        .filter(comp_func(Flowspec6.expires, today))
        .order_by(Flowspec6.expires.desc())
        .all()
    )
    rules_rtbh = (
        db.session.query(RTBH)
        .filter(RTBH.rstate_id == 1)
        .filter(comp_func(RTBH.expires, today))
        .order_by(RTBH.expires.desc())
        .all()
    )

    messages_v4 = [messages.create_ipv4(rule, action) for rule in rules4]
    messages_v6 = [messages.create_ipv6(rule, action) for rule in rules6]
    messages_rtbh = [messages.create_rtbh(rule, action) for rule in rules_rtbh]

    messages_all = []
    messages_all.extend(messages_v4)
    messages_all.extend(messages_v6)
    messages_all.extend(messages_rtbh)

    author_action = "announce all" if action == constants.ANNOUNCE else "withdraw all expired"

    for command in messages_all:
        route = Route(
            author=f"System call / {author_action} rules",
            source=RouteSources.UI,
            command=command,
        )
        announce_route(route)

    if action == constants.WITHDRAW:
        for ruleset in [rules4, rules6, rules_rtbh]:
            for rule in ruleset:
                rule.rstate_id = 2

        db.session.commit()
