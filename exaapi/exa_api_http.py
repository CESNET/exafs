#!/usr/bin/env python
"""
ExaBGP HTTP API process
This module is process for ExaBGP
https://github.com/Exa-Networks/exabgp/wiki/Controlling-ExaBGP-:-possible-options-for-process

Each command received in the POST request is send to stdout and captured by ExaBGP.
"""

from flask import Flask, request, abort
from sys import stdout

import exa_api_logger

app = Flask(__name__)

logger = exa_api_logger.create()


@app.route('/', methods=['POST'])
def command():
    cmd = request.form['command']
    logger.info(cmd)
    stdout.write('%s\n' % cmd)
    stdout.flush()

    return '%s\n' % cmd


if __name__ == '__main__':
    app.run()
