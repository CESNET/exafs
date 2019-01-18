"""
Module for message announcing and logging
"""
from datetime import datetime

import requests
from flask import current_app, session

from flowapp import db, messages
from flowapp.models import Log

ROUTE_MODELS = {1: messages.create_rtbh, 4: messages.create_ipv4, 6: messages.create_ipv6}
RULE_TYPES = {'RTBH': 1, 'IPv4': 4, 'IPv6': 6}

def announce_route(route):
    """
    Announce route to ExaAPI

    @TODO take the request away, use some kind of messaging (maybe celery?)
    """
    if not current_app.config['TESTING']:
        requests.post('http://localhost:5000/', data={'command': route})


def log_route(user_id, route_model, rule_type):
    """
    Convert route to EXAFS message and log it to database
    :param user_id : int curent user
    :param route_model: model with route object
    :param rule_type: string
    :return: None
    """
    converter = ROUTE_MODELS[rule_type]
    task = converter(route_model)
    log = Log(time=datetime.now(),
              task=task,
              rule_type=rule_type,
              rule_id=route_model.id,
              user_id=user_id)
    db.session.add(log)
    db.session.commit()


def log_withdraw(user_id, task, rule_type, deleted_id):
    """
    Log the withdraw command to database
    :param task: command message
    """
    log = Log(time=datetime.now(),
              task=task,
              rule_type=rule_type,
              rule_id=deleted_id,
              user_id=user_id)
    db.session.add(log)
    db.session.commit()

