#!/bin/bash

# Запускаем скрипты последовательно
poetry run python main1.py
poetry run python db_backup.py
