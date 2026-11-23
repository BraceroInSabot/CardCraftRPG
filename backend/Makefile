test_bf_push:
	coverage run -m pytest -rA --no-header --html=./tests/reports/pytest/report.html --self-contained-html && coverage html

up:
	docker-compose up -d --build

migrate:
	python manage.py makemigrations
	python manage.py migrate

env:
	cp .env.example .env