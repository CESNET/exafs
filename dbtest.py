from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import models
import config

app = Flask(__name__)

# Configurations
if path.realpath(__file__) == '/home/albert/work/flowspec/www/flowapp.py':
    app.config.from_object(config.DevelopmentConfig)
else: 
    app.config.from_object(config.ProductionConfig)
    
db = SQLAlchemy(app)


if __name__ == "__main__":
    db.create_all()        