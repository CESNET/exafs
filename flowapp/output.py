"""
Module for message announcing and logging
"""
from datetime import datetime

import requests
import pika
from flask import current_app, session

from flowapp import db, messages
from flowapp.models import Log

ROUTE_MODELS = {1: messages.create_rtbh, 4: messages.create_ipv4, 6: messages.create_ipv6}
RULE_TYPES = {'RTBH': 1, 'IPv4': 4, 'IPv6': 6}

def announce_route(route):
    """
    Dispatch route to ExaBGP API 
    API must be set in app config.py 
    defaults to HTTP API
    """
    if current_app.config['EXA_API'] == 'RABBIT':
        announce_to_rabbitmq(route)
    else:
        announce_to_http(route)

def announce_to_http(route):
    """
    Announce route to ExaBGP HTTP API process 
    """
    if not current_app.config['TESTING']:
        try:
            resp = requests.post(current_app.config['EXA_API_URL'], data={'command': route})
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print("ExaAPI HTTP Error: ", err)
        except requests.exceptions.RequestException as ce:
            print("Connection to ExaAPI failed: ", ce)
    else:
        print("Testing:", route)        
            
def announce_to_rabbitmq(route):
    """
    Announce rout to ExaBGP RabbitMQ API process
    """
    if not current_app.config['TESTING']:
        user = current_app.config['EXA_API_RABBIT_USER']
        passwd = current_app.config['EXA_API_RABBIT_PASS']
        queue = current_app.config['EXA_API_RABBIT_QUEUE']
        credentials = pika.PlainCredentials(user, passwd)
        parameters = pika.ConnectionParameters(current_app.config['EXA_API_RABBIT_HOST'],
                                            current_app.config['EXA_API_RABBIT_PORT'],
                                            '/',
                                            credentials)

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='',
                      routing_key=queue,
                      body=route)
    else:
        print("Testing:", route)        

def log_route(user_id, route_model, rule_type, author):
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
              user_id=user_id,
              author=author)
    db.session.add(log)
    db.session.commit()


def log_withdraw(user_id, task, rule_type, deleted_id, author):
    """
    Log the withdraw command to database
    :param task: command message
    """
    log = Log(time=datetime.now(),
              task=task,
              rule_type=rule_type,
              rule_id=deleted_id,
              user_id=user_id,
              author=author
            )
    db.session.add(log)
    db.session.commit()

