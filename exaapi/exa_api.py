#!/usr/bin/env python
"""
This module is used as simple echo
each command received in the POST request is send to stdout
"""
from flask import Flask, request
from sys import stdout

app = Flask(__name__)

@app.route('/', methods=['POST'])
def command():
    cmd = request.form['command']
    stdout.write('%s\n' % cmd)
    stdout.flush()

    return '%s\n' % cmd


if __name__ == '__main__':
    app.run()
