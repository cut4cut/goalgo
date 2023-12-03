APP_NAME = goalgo
PWD = $(shell pwd)

env:
	@$(eval SHELL:=/bin/bash)
	@cp .env.template .env

docker-build:
	docker build --tag $(APP_NAME):latest .

docker-run:
	docker run --env-file .env -p 8000:8000 $(APP_NAME):latest 

docker-push:
	sudo docker image tag $(APP_NAME) cut4cut/$(APP_NAME):1.0
	sudo docker image push cut4cut/$(APP_NAME):1.0

run:
	python3 -m trading_service

format:
	isort .
	ruff format .
	
lint:
	ruff check .
	pyright