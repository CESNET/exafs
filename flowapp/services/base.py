from flowapp import messages
from flowapp.constants import ANNOUNCE, WITHDRAW
from flowapp.models import RTBH
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
