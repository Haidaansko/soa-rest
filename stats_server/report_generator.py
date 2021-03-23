import os
import pika
import sys
import json

from src.config import IMG_PATH, PDF_PATH, RABBITMQ_HOST

from fpdf import FPDF


def generate_report(player_dict):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 15)
    avatar_fname = player_dict.get('avatar', None)
    if avatar_fname:
        pdf.image(name=str(IMG_PATH / avatar_fname), w=70, h=70)

    for k in ('username', 'gender', 'email', 'total_sessions', 'total_victories', 'total_defeats', 'total_time'):
        pdf.cell(70, 10, f'{k}: {player_dict[k]}', ln=1)
    path = str(PDF_PATH / f"{player_dict['id']}.pdf")
    pdf.output(path).encode('latin-1')
    return path


def main():

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue='report_gen')

    def callback(ch, method, properties, body):
        print(' [*] Data received')
        path = generate_report(json.loads(body.decode('utf-8')))
        print(f' [*] PDF created: {path}')

    channel.basic_consume(queue='report_gen',
                          on_message_callback=callback, auto_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
