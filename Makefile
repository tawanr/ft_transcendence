include .env
export

r:
	@echo "no default"

req:
	pip freeze > backend/requirements.txt

migrate:
	cd backend && python manage.py migrate

backend:
	cd backend && python manage.py runserver 0.0.0.0:8000

.PHONY: all migrate backend