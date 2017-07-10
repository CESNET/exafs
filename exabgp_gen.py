#!/usr/bin/env python

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import environ
import sys
import time

import config
import messages


app = Flask(__name__)


# Configurations
try:
    env = environ['USERNAME']
except KeyError as e:
    env = 'Production'
    
if env=='albert':
    app.config.from_object(config.DevelopmentConfig)
else: 
    app.config.from_object(config.ProductionConfig)

db = SQLAlchemy(app)

import models

rules4 = db.session.query(models.Flowspec4).order_by(models.Flowspec4.expires.desc()).all()
rules6 = db.session.query(models.Flowspec6).order_by(models.Flowspec6.expires.desc()).all()
rules = {4: rules4, 6: rules6}

actions = db.session.query(models.Action).all()
actions = {action.id: action for action in actions}

rules_rtbh = db.session.query(models.RTBH).order_by(models.RTBH.expires.desc()).all()

output = [messages.create_message_from_rule(rule) for rule in rules4]

for message in output:
    sys.stdout.write(message + '\n')
    sys.stdout.flush()    
#   sys.stdout.write("show neighbor summary") 

now = time.time()
while True and time.time() < now + 20:
    if 'shutdown' in sys.stdin.readline():
        break
    time.sleep(1)