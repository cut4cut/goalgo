APP_NAME = goalgo
PWD = $(shell pwd)

env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.example .env

up:
	docker-compose up --build

down:
	docker-compose down --remove-orphans

docker-build:
	docker build --tag $(APP_NAME):latest .

docker-run:
	docker run --env-file .env -p 8000:8000 $(APP_NAME):latest 

docker-push:
	sudo docker image tag $(APP_NAME) cut4cut/$(APP_NAME):1.0
	sudo docker image push cut4cut/$(APP_NAME):1.0

run-strategy:
	python3 -m trading_service

run-adminka:
	uvicorn admin_service.app:app --reload

format:
	isort .
	ruff format .
	
lint:
	ruff check .
	pyright