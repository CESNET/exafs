from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config
from os import environ

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

from models import *

print "#: cleaning database"
db.reflect()
db.drop_all()
print "#: creating tables"
db.create_all()   

users = [
        {"name": "jiri.vrany@tul.cz", "role_id": 3, "org_id": 1},
        {"name": "petr.adamec@tul.cz", "role_id": 3, "org_id": 1} 
    ]
print "#: inserting users"
insert_users(users)         