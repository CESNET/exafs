from datetime import datetime, timedelta

from sqlalchemy import select
from flowapp.constants import RuleTypes
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

    @classmethod
    def get_recent_paginated(cls, page: int, per_page: int = 20, weeks: int = 1):
        since = datetime.now() - timedelta(weeks=weeks)
        return db.paginate(
            select(cls).filter(cls.time > since).order_by(cls.time.desc()),
            page=page,
            per_page=per_page,
            max_per_page=None,
            error_out=False,
        )

    @classmethod
    def delete_old(cls, days: int = 30):
        """Delete logs older than :param days from the database"""
        cls.query.filter(cls.time < datetime.now() - timedelta(days=days)).delete()
        db.session.commit()

    def __repr__(self):
        return f"<Log {self.id}>"

    def __str__(self):
        """
        {"author": "vrany@cesnet.cz / Cel\u00fd sv\u011bt", "source": "UI", "command": "cmd"}
        """
        return f"{self.author} - {RuleTypes(self.rule_type).name}({self.rule_id}) - {self.task}"
