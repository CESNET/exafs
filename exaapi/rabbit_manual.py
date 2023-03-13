import pika
import sys

import config

user = config.EXA_API_RABBIT_USER
passwd = config.EXA_API_RABBIT_PASS
queue = config.EXA_API_RABBIT_QUEUE
credentials = pika.PlainCredentials(user, passwd)
parameters = pika.ConnectionParameters(config.EXA_API_RABBIT_HOST,
                                    config.EXA_API_RABBIT_PORT,
                                    config.EXA_API_RABBIT_VHOST,
                                    credentials)

connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue=queue)    
route = sys.argv[1]

print("got :", route)

channel.basic_publish(exchange='',
                routing_key=queue,
                body=route)