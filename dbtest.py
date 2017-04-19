from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import config
from os import environ

app = Flask(__name__)

# Configurations
try:
    env = environ['APP_ENV']
except KeyError as e:
    env = 'Production'
    
if env=='Devel':
    app.config.from_object(config.DevelopmentConfig)
else: 
    app.config.from_object(config.ProductionConfig)

db = SQLAlchemy(app)

from models import *

db.create_all()        