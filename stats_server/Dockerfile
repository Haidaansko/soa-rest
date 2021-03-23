FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY src/*.py ./src/
COPY ./*.py ./

EXPOSE 5000

CMD ["python", "app.py"]