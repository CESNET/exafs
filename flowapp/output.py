"""
Module for message announcing and logging
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Union, Callable, Any

import requests
import pika
import json
from flask import current_app

from flowapp import db, messages
from flowapp.constants import RuleTypes
from flowapp.models import Log
from flowapp.models import Flowspec4, Flowspec6, RTBH


ROUTE_MODELS: Dict[int, Callable[[Any], str]] = {
    1: messages.create_rtbh,
    4: messages.create_ipv4,
    6: messages.create_ipv6,
}


class RouteSources:
    UI: str = "UI"
    API: str = "API"


@dataclass
class Route:
    author: str
    source: str  # Using str instead of RouteSources for flexibility
    command: str

    def __dict__(self) -> Dict[str, str]:
        return asdict(self)


def announce_route(route: Route) -> None:
    """
    Dispatch route as dict to ExaBGP API
    API must be set in app config.py
    defaults to HTTP API
    """
    current_app.logger.debug(asdict(route))
    if current_app.config.get("EXA_API") == "RABBIT":
        announce_to_rabbitmq(asdict(route))
    else:
        announce_to_http(asdict(route))


def announce_to_http(route: Dict[str, str]) -> None:
    """
    Announce route to ExaBGP HTTP API process
    """
    if not current_app.config["TESTING"]:
        try:
            resp = requests.post(current_app.config["EXA_API_URL"], data={"command": json.dumps(route)})
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            current_app.logger.error("ExaAPI HTTP Error: ", err)
        except requests.exceptions.RequestException as ce:
            current_app.logger.error("Connection to ExaAPI failed: ", ce)
    else:
        current_app.logger.debug(f"Testing: {route}")


def announce_to_rabbitmq(route: Dict[str, str]) -> None:
    """
    Announce rout to ExaBGP RabbitMQ API process
    """
    if not current_app.config["TESTING"]:
        user = current_app.config["EXA_API_RABBIT_USER"]
        passwd = current_app.config["EXA_API_RABBIT_PASS"]
        queue = current_app.config["EXA_API_RABBIT_QUEUE"]
        credentials = pika.PlainCredentials(user, passwd)
        parameters = pika.ConnectionParameters(
            current_app.config["EXA_API_RABBIT_HOST"],
            current_app.config["EXA_API_RABBIT_PORT"],
            current_app.config["EXA_API_RABBIT_VHOST"],
            credentials,
        )

        with pika.BlockingConnection(parameters) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=queue)
            channel.basic_publish(exchange="", routing_key=queue, body=json.dumps(route))
    else:
        current_app.logger.debug(f"Testing: {route}")


def log_route(user_id: int, route_model: Union[RTBH, Flowspec4, Flowspec6], rule_type: RuleTypes, author: str) -> None:
    """
    Convert route to EXAFS message and log it to database
    :param user_id : int curent user
    :param route_model: model with route object (RTBH, Flowspec4, or Flowspec6)
    :param rule_type: RuleTypes enum
    :param author: str name of the author
    :return: None
    """
    rule_type_value = rule_type.value
    converter = ROUTE_MODELS[rule_type_value]
    task = converter(route_model)
    log = Log(
        time=datetime.now(),
        task=task,
        rule_type=rule_type_value,
        rule_id=route_model.id,
        user_id=user_id,
        author=author,
    )
    db.session.add(log)
    current_app.logger.info(log)
    db.session.commit()


def log_withdraw(user_id: int, task: str, rule_type: RuleTypes, deleted_id: int, author: str) -> None:
    """
    Log the withdraw command to database
    :param user_id: int user ID
    :param task: str command message
    :param rule_type: RuleTypes enum
    :param deleted_id: int ID of deleted rule
    :param author: str name of the author
    :return: None
    """
    log = Log(
        time=datetime.now(),
        task=task,
        rule_type=rule_type.value,
        rule_id=deleted_id,
        user_id=user_id,
        author=author,
    )
    db.session.add(log)
    current_app.logger.info(log)
    db.session.commit()
