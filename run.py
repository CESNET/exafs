from os import environ
from flowapp import app, db
import config

# Configurations
try:
    env = environ['USERNAME']
except KeyError as e:
    env = 'Production'

if env == 'albert':
    app.config.from_object(config.DevelopmentConfig)
else:
    app.config.from_object(config.ProductionConfig)

# init database object
db.init_app(app)
# run app
app.run(host='0.0.0.0', port=8080, debug=True)