#!/bin/bash

pip install --user -r backend/requirements.txt
apt update && apt upgrade -y
apt install -y nginx
