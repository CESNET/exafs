#!/usr/bin/env python
"""
This module is used as simple echo
each command received in the POST request is send to stdout
"""
import logging
from flask import Flask, request
from sys import stdout

app = Flask(__name__)

#logovani
logger = logging.getLogger(__name__)
f_format = logging.Formatter('%(asctime)s:  %(message)s')
f_handler = logging.FileHandler('/var/log/exabgp/exa_api.log')
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
