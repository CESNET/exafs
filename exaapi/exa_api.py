#!/usr/bin/env python
"""
This module is process for ExaBGP
https://github.com/Exa-Networks/exabgp/wiki/Controlling-ExaBGP-:-possible-options-for-process

Each command received in the POST request is send to stdout and captured by ExaBGP.
"""
import logging
from flask import Flask, request
from sys import stdout

import config

app = Flask(__name__)

#logovani
logger = logging.getLogger(__name__)
f_format = logging.Formatter(config.LOG_FORMAT)
f_handler = logging.FileHandler(config.LOG_FILE)
f_handler.setFormatter(f_format)
logger.setLevel(logging.INFO)
logger.addHandler(f_handler)


@app.route('/', methods=['POST'])
def command():
    cmd = request.form['command']
    logger.info(cmd)
    stdout.write('%s\n' % cmd)
    stdout.flush()
    

    return '%s\n' % cmd


if __name__ == '__main__':
    app.run()
