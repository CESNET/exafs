from datetime import datetime

from flask import Flask, session, redirect
from flask_sso import SSO
from app import create_app

def wsgi(*args, **kwargs):
    return create_app()(*args, **kwargs)


if __name__ == '__main__':
    create_app().run(debug=True)
