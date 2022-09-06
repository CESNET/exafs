#!/usr/bin/env python
"""
ExaBGP RabbitMQ API process
This module is process for ExaBGP
https://github.com/Exa-Networks/exabgp/wiki/Controlling-ExaBGP-:-possible-options-for-process

Each command received from the queue is send to stdout and captured by ExaBGP.
"""

import pika, sys, os

import config
import exa_api_logger

logger = exa_api_logger.create()

def main():
    user = config.EXA_API_RABBIT_USER
    passwd = config.EXA_API_RABBIT_PASS
    queue = config.EXA_API_RABBIT_QUEUE
    credentials = pika.PlainCredentials(user, passwd)
    parameters = pika.ConnectionParameters(config.EXA_API_RABBIT_HOST,
                                        config.EXA_API_RABBIT_PORT,
                                        '/',
                                        credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue=queue)                                        

    def callback(ch, method, properties, body):
        body = body.decode("utf-8") 
        logger.info(body)
        sys.stdout.write('%s\n' % body)
        sys.stdout.flush()

    channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)