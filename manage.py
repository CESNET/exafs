from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from os import environ

from flowapp import app, db
import config


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

migrate = Migrate(app, db)

manager = Manager(app)

manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()