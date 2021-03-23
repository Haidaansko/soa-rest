import os
import pathlib

IMG_PATH = pathlib.Path('./img').absolute()
PDF_PATH = pathlib.Path('./pdf').absolute()
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

IMG_PATH.mkdir(parents=True, exist_ok=True)
PDF_PATH.mkdir(parents=True, exist_ok=True)
