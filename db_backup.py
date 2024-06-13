import subprocess
import os
from datetime import datetime
import schedule
import time

# Создание директории для дампов, если она не существует
if not os.path.exists('dumps'):
    os.makedirs('dumps')


def create_dump(database, user, host, password, port='5432'):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dump_file = os.path.join('dumps', f'{database}_dump_{timestamp}.sql')
    command = [
        'pg_dump',
        '-h', host,
        '-U', user,
        '-d', database,
        '-F', 'c',
        '-f', dump_file
    ]

    # Установим переменную окружения для пароля PostgreSQL
    os.environ['PGPASSWORD'] = password

    try:
        subprocess.run(command, check=True)
        print(f"Database dump created successfully: {dump_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating database dump: {e}")
    finally:
        del os.environ['PGPASSWORD']


def job():
    database = os.getenv('DATABASE_NAME')
    user = os.getenv('DATABASE_USER')
    host = os.getenv('DATABASE_HOST')
    password = os.getenv('DATABASE_PASSWORD')

    create_dump(
        database=database,
        user=user,
        host=host,
        password=password,
        port='5432'
    )


# Планируем выполнение задачи каждый день в 12:00
schedule.every().day.at("12:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
