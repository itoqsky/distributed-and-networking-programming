import json
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'co2.sensor'


if __name__ == '__main__':
    
    try:
        with BlockingConnection( ConnectionParameters(host=RMQ_HOST, credentials=PlainCredentials(RMQ_USER, RMQ_PASS))) as connection:
            channel = connection.channel()
            while True:
                channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=ExchangeType.topic, durable= True)
                channel.queue_declare(queue=ROUTING_KEY, durable=True)
                channel.queue_bind(exchange=EXCHANGE_NAME, queue=ROUTING_KEY, routing_key=ROUTING_KEY)
                
                lvl = input("Enter CO2 level: ")

                time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                message = {'time': time_str, 'value': lvl}

                json_string = json.dumps(message, default=str)
                channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json_string)
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit()
