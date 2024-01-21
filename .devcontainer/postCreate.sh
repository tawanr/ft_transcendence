#!/bin/bash

pip install --user -r backend/requirements.txt
sudo apt update && sudo apt upgrade -y
sudo apt install -y nginx
