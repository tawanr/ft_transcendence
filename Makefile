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

test:
	cd backend && python manage.py test $(var)

shell:
	cd backend && python manage.py shell

run-nginx:
	sudo nginx -c $(PWD)/nginx/default.conf
	sudo nginx -s reload

stop-nginx:
	sudo nginx -s stop

.PHONY: all migrate backend shell mm
