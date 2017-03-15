from datetime import datetime

from flask import Flask


def time_string():
    t = datetime.now().time()
    return '{0:02d}:{1:02d}:{2:02d}'.format(t.hour, t.minute, t.second)


def create_app():
    app = Flask('SSOTutorial')

    @app.route('/')
    def index():
        t = time_string()
        return '<h1>Hello, World!</h1><h2>Server time: {0}</h2>'.format(t)

    return app


def wsgi(*args, **kwargs):
    return create_app()(*args, **kwargs)


if __name__ == '__main__':
    create_app().run()
