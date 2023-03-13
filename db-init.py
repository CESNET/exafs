
from flask import Flask
from flowapp import db
from flowapp.models import *

import config
from os import environ


def create_app():
    app = Flask('FlowSpecDB init')
    # Configurations
    try:
        env = environ['USERNAME']
    except KeyError as e:
        env = 'Production'

    if env == 'albert':
        print("DEVEL")
        app.config.from_object(config.DevelopmentConfig)
    else:
        print("PRODUCTION")
        app.config.from_object(config.ProductionConfig)

    db.init_app(app)

    with app.app_context():
        print("#: cleaning database")
        db.reflect()
        db.drop_all()
        print("#: creating tables")
        db.create_all()


    return app


if __name__ == '__main__':
    create_app().app_context().push()
