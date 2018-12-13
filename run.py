from os import environ

from flowapp import app, db
import config

# Configurations
try:
    env = environ['EXAFS_ENV']
except KeyError as e:
    env = 'Production'

if env == 'devel':
    app.config.from_object(config.DevelopmentConfig)
else:
    app.config.from_object(config.ProductionConfig)

# init database object
db.init_app(app)

# run app
if __name__ == '__main__':
    app.run(host='::', port=8080, debug=True)
