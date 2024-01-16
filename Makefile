include .env
export

r:
	@echo "no default"

req:
	pip freeze > backend/requirements.txt

migrate:
	cd backend && python manage.py migrate

mm:
	cd backend && python manage.py makemigrations

backend:
	cd backend && python manage.py runserver 0.0.0.0:8000

shell:
	cd backend && python manage.py shell

run-nginx:
	sudo nginx -c $(PWD)/nginx/nginx.conf
	sudo nginx -s reload

stop-nginx:
	sudo nginx -s stop

.PHONY: all migrate backend shell mm