# goalgo

## Описание проекта

Есть два сервиса:

1. Обертка вокруг стратегии [trading_service](https://github.com/cut4cut/goalgo/tree/main/trading_service)
2. Мониторинг/админка стратегии [admin_service](https://github.com/cut4cut/goalgo/tree/main/admin_service)

Данные из сервиса обертки шлются через декоратор [@observeit](https://github.com/cut4cut/goalgo/blob/main/trading_service/pkg/observer.py#L39) в сервис админки. Из админки данные можно достать через HTTP API. Сваггер доступен по адресу `/schema/swagger`

## Запуск trading_service и admin_service локально

Выбор нужной версии python:
```shell
pyenv shell 3.10
```
Создане виртуального окружения:
```shell
poetry install
poetry shell
```
Настройка перменных окружения:
```shell
make env
```
Запуск БД;
```shell
make up
```
Запуск самого сервиса:
```shell
make run-strategy
make run-adminka
```