import json
import os
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'rep.*'

def get_value(line):
    dic = json.loads(line)
    return int(dic['value'])

def callback(channel, method, properties, body):
    with open("receiver.log", "r") as f:
        msg = json.loads(body)
        lines = f.readlines()

        if msg['query'] == 'current' :
            lvl = json.loads(lines[-1]).get('value')
            print(f"{msg['time']}: Latest CO2 level is {lvl}")
        elif msg['query'] == 'average':
            values = list(map(get_value, lines))
            avg = sum(values) / len(values)
            print(f"{msg['time']}: Average CO2 level is {avg}")


if __name__ == '__main__':
    try:
        with BlockingConnection(ConnectionParameters(host=RMQ_HOST,credentials=PlainCredentials(RMQ_USER, RMQ_PASS))) as connection:
            channel = connection.channel()

            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=ExchangeType.topic, durable= True)

            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name , routing_key = ROUTING_KEY)

            print(' [*] Waiting for queries from the control tower. To exit press CTRL+C')

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            
            channel.start_consuming()
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit()
