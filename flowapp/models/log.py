from .base import db


class Log(db.Model):
    """Log model for system actions"""

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    task = db.Column(db.String(1000))
    author = db.Column(db.String(1000))
    rule_type = db.Column(db.Integer)
    rule_id = db.Column(db.Integer)
    user_id = db.Column(db.Integer)

    def __init__(self, time, task, user_id, rule_type, rule_id, author):
        self.time = time
        self.task = task
        self.rule_type = rule_type
        self.rule_id = rule_id
        self.user_id = user_id
        self.author = author
