import json

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'co2.*'


def callback(channel, method, properties, body):
    msg = json.loads(body)
    with open("receiver.log", "a") as f:
        f.write(body.decode() + '\n')
    if(int(msg['value']) > 500):
        print(f"{msg['time']}: WARNING")
    else:
        print(f"{msg['time']}: OK")


if __name__ == '__main__':
    try:
        with BlockingConnection(ConnectionParameters(host=RMQ_HOST,credentials=PlainCredentials(RMQ_USER, RMQ_PASS))) as connection:
            channel = connection.channel()

            channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type=ExchangeType.topic, durable= True)

            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name , routing_key = ROUTING_KEY)

            print(' [*] Waiting for CO2 level. To exit press CTRL+C')

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

            channel.start_consuming()
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit()