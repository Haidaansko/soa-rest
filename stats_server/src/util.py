import os
import hashlib
import imghdr
import json
import pika

from .config import RABBITMQ_HOST


def pwd_enc(pwd):
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()


def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    img_format = imghdr.what(None, header)
    if not img_format:
        return None
    return '.' + img_format


def request_report_gen(user):
    def make_data(user):
        result = user.to_dict()
        result.update(user.stats.to_dict())
        result['id'] = user.id
        result['username'] = user.username
        return json.dumps(result)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='report_gen')
    body = make_data(user).encode('utf-8')
    channel.basic_publish(exchange='', routing_key='report_gen',
                          body=body)
    print(" [x] PDF request sent")
    connection.close()
