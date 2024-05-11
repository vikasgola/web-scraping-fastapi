FROM python:3.9
ENV PYTHONUNBUFFERED 1

RUN apt-get update
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
