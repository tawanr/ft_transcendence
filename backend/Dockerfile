FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED 1

RUN apt update -y
RUN apt-get install gcc g++ musl-dev -y
RUN apt-get install postgresql postgresql-contrib -y
RUN apt-get install netcat-openbsd -y
COPY ./requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt

WORKDIR /opt/app-root/
COPY ./ /opt/app-root/
