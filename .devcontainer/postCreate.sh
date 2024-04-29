#!/bin/bash

pip install --upgrade pip
pip install --user --no-cache-dir -r backend/requirements.txt
apt update && apt upgrade -y
apt-get install gcc g++ musl-dev -y
apt-get install postgresql postgresql-contrib -y
apt-get install netcat-openbsd -y
apt install -y nginx
