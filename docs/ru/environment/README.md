# Окружение

[Оглавление](../README.md)

Проект использует Python 3.14.7 и Pipenv. Точная версия Python указана в `Pipfile`, зависимости фиксируются в `Pipfile.lock`. Для загрузки конфигурации установлен `toml==0.10.2`.

[Python 3.14.7](https://www.python.org/downloads/release/python-3147/) — стабильный выпуск от 5 августа 2026 года. Настройка проверена с Pipenv 2026.8.0; в созданном окружении установлен pip 26.2.1.

## Настройка в Windows

После установки Python 3.14.7 при необходимости установите Pipenv:

```powershell
py -3.14 -m pip install pipenv==2026.8.0
```

В корне проекта выполните:

```powershell
$env:PIPENV_VENV_IN_PROJECT = "1"
$env:PIPENV_IGNORE_VIRTUALENVS = "1"
py -3.14 -m pipenv sync
```

Окружение создаётся в `.venv` внутри проекта и исключено из Git. Переменные выше задавайте в каждой новой сессии настройки. Файлы `Pipfile` и `Pipfile.lock` хранятся в Git.

## Запуск и проверка

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip --version
py -3.14 -m pipenv --venv
py -3.14 -m pipenv verify
py -3.14 -m pipenv run python --version
```

Для IDE выберите интерпретатор `.venv\Scripts\python.exe`. Активация необязательна при прямом запуске интерпретатора или использовании `pipenv run`.

Новые зависимости добавляйте через Pipenv с точной версией; вместе с `Pipfile` обновляйте `Pipfile.lock`. Пакеты проекта должны устанавливаться только в его локальное окружение.

## Конфигурация

`src/settings.py` читает локальный `src/config.toml`; если его нет, используется `src/default_config.toml`. Оба TOML-файла пока не содержат параметров. Загрузка выполняется библиотекой `toml==0.10.2`, зафиксированной в Pipenv.

Локальный `src/config.toml` исключён из Git. После клонирования при необходимости создайте его копированием `src/default_config.toml`. Общие значения по умолчанию храните в шаблоне, локальные настройки — в `config.toml`. Локальный файл полностью заменяет шаблон, значения не объединяются.
