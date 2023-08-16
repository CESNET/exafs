"""
This is an example of how to run the application.
First copy the file as run.py (or whatever you want)
Then edit the file to match your needs.
In general you should not need to edit this example file.
Only if you want to configure the application main menu and
dashboard. Or in case that you want to add extensions etc.
"""

from os import environ

from flowapp import create_app, db
import config

# Configurations
env = environ.get('EXAFS_ENV', 'Production')


if env == 'devel':
    config_obj = config.DevelopmentConfig()
    config_obj.DEVEL = True
else:
    config_obj = config.ProductionConfig()
    config_obj.SESSION_COOKIE_SECURE = True
    config_obj.SESSION_COOKIE_HTTPONLY = True
    config_obj.SESSION_COOKIE_SAMESITE = 'Lax'
    config_obj.DEVEL = False

# Call app factory
app = create_app(config=config_obj)

app.config.from_object(config_obj)

# init database object
db.init_app(app)

# run app
if __name__ == '__main__':
    app.run(host='::', port=8080, debug=True)
