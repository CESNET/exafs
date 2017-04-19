from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import models

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:my-secret-pw@127.0.0.1:3306/flowtest?host=127.0.0.1?port=3306'
db = SQLAlchemy(app)


if __name__ == "__main__":
    db.create_all()        