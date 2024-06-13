import os
import subprocess

import psycopg2
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import schedule
import time

# Установите переменные окружения
DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'car_data')
DATABASE_USER = os.getenv('DATABASE_USER', 'postgres')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '123')
SELENIUM_HOST = os.getenv('SELENIUM_HOST', 'localhost')
SELENIUM_PORT = os.getenv('SELENIUM_PORT', '4444')
SELENIUM_URL = f'http://{SELENIUM_HOST}:{SELENIUM_PORT}/wd/hub'

stock_url = 'https://auto.ria.com/uk/car/used/?page='

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--disable-infobars')


def create_table_if_not_exists(connection):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        url TEXT,
        title TEXT,
        price_usd INTEGER,
        odometer INTEGER,
        username TEXT,
        phone_number TEXT,
        image_url TEXT,
        images_count INTEGER,
        car_number TEXT,
        car_vin TEXT,
        datetime_found TIMESTAMP
    );
    """
    cursor = connection.cursor()
    cursor.execute(create_table_query)
    connection.commit()
    cursor.close()


def find_max_page(url):
    response = requests.get(url + '1')
    soup = BeautifulSoup(response.content, 'lxml')
    max_page = soup.find('nav', class_='unstyle pager').find_all('span', class_='page-item mhide')[
        -1].text.strip().replace(' ', '')
    return int(max_page)


def collect_all_url_posts(max_page):
    url_posts = []
    for i in range(1, 4):
        response = requests.get(stock_url + str(i))
        soup = BeautifulSoup(response.text, 'lxml')
        all_posts_in_page = soup.find_all('section', class_='ticket-item')
        for post in all_posts_in_page:
            url_post = post.find('a', class_='address').attrs['href']
            url_posts.append(url_post)
            print('[INFO] Added post {}'.format(url_post))
        url_posts = list(set(url_posts))
    return url_posts


def extract_price_usd(soup, url):
    try:
        price_div = soup.find('div', class_='price_value')
        if price_div and '$' in price_div.text:
            return int(price_div.find('strong').text.strip().replace(' ', '').replace('$', ''))
        additional_price_div = soup.find('div', class_='price_value price_value--additional')
        if additional_price_div and '$' in additional_price_div.text:
            return int(additional_price_div.text.strip().replace('$', '').replace(' ', ''))
        span = additional_price_div.find('span')
        if span and '$' in span.text:
            return int(span.find('span').text.strip().replace('$', '').replace(' ', ''))
    except Exception as e:
        print(f"Error extracting price for {url}: {e}")
    return 0


def extract_odometer(soup, url):
    try:
        return int(soup.find('div', class_='base-information bold').text.strip().split(' ')[0]) * 1000
    except Exception as e:
        print(f"Error extracting odometer for {url}: {e}")
        return 0


def extract_user_name(soup, url):
    try:
        return soup.find('div', class_='seller_info_name bold').text.strip()
    except Exception:
        try:
            return soup.find('h4', class_='seller_info_name').find('a').text.strip()
        except Exception as e:
            print(f"Error extracting user name for {url}: {e}")
            return 'Empty'


def extract_image_count(soup, url):
    try:
        return int(soup.find('a', class_='show-all link-dotted').text.strip().split(' ')[2])
    except Exception as e:
        print(f"Error extracting image count for {url}: {e}")
        return 0


def extract_car_number(soup, url):
    try:
        return soup.find('span', class_='state-num ua').next.text.strip()
    except Exception as e:
        print(f"Error extracting car number for {url}: {e}")
        return 0


def extract_car_vin(soup, url):
    try:
        return soup.find_all('span', class_='label-vin')[-1].text.strip()
    except Exception:
        try:
            return soup.find_all('span', class_='vin-code')[-1].text.strip()
        except Exception as e:
            print(f"Error extracting car VIN for {url}: {e}")
            return 0


def get_phone_number(url):
    with webdriver.Remote(command_executor=SELENIUM_URL, options=options) as driver:
        driver.get(url)
        driver.maximize_window()
        time.sleep(2)
        driver.execute_script("window.scrollBy(0,350)")
        try:
            driver.find_element(By.XPATH, '//*[@id="phonesBlock"]/div/span/span').click()
        except Exception as e:
            print(e)
            try:
                driver.find_element(By.XPATH, '//*[@id="react-phones"]/div[1]/span/span[1]').click()
            except Exception as e:
                print(e)
        time.sleep(2)
        try:
            phone_number = driver.find_element(By.XPATH, '//*[@id="openCallMeBack"]/div[2]/div[2]').text
        except Exception as e:
            print(e)
            try:
                phone_number = driver.find_element(By.XPATH,
                                                   '/html/body/section/div[1]/div[2]/div/section/div[5]/a').text
            except:
                phone_number = None
                print('Bad number')
        return phone_number


def get_info_with_out_phone_number(connection, urls_posts: list):
    counter_at_now = 0
    for url_post in urls_posts:
        if 'newauto' in url_post:
            counter_at_now += 1
            print(f'[INFO NEW CAR] New automobile post skipped, {counter_at_now} / {len(urls_posts)}')
            continue
        counter_at_now += 1
        print(f'[INFO] Processing post {url_post}, {counter_at_now} / {len(urls_posts)}')
        response = requests.get(url_post, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')

        title = soup.find('h1', class_='head').text.strip() if soup.find('h1', class_='head') else 'Empty'
        price_usd = extract_price_usd(soup, url_post)
        odometer = extract_odometer(soup, url_post)
        user_name = extract_user_name(soup, url_post)
        phone_number = get_phone_number(url_post)
        image_url = soup.find('img', class_='outline m-auto').attrs['src'] if soup.find('img',
                                                                                        class_='outline m-auto') else 'Empty'
        image_count = extract_image_count(soup, url_post)
        car_number = extract_car_number(soup, url_post)
        car_vin = extract_car_vin(soup, url_post)

        insert_car_data(connection, url_post, title, price_usd, odometer, user_name, phone_number, image_url,
                        image_count,
                        car_number, car_vin)


def insert_car_data(connection, url, title, price_usd, odometer, username, phone_number, image_url, images_count,
                    car_number, car_vin):
    try:
        cursor = connection.cursor()

        # Текущая дата и время
        datetime_found = datetime.now()

        # SQL запрос для вставки данных
        insert_query = """
        INSERT INTO cars (url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin, datetime_found)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        record_to_insert = (
            url, title, price_usd, odometer, username, phone_number, image_url, images_count, car_number, car_vin,
            datetime_found)
        cursor.execute(insert_query, record_to_insert)

        # Сохранение изменений
        connection.commit()
        print("Record inserted successfully")

    except (Exception, psycopg2.Error) as error:
        print("Error while inserting data into PostgreSQL", error)

    finally:
        if cursor:
            cursor.close()


def dump_database():
    # Получение параметров для подключения к базе данных из переменных окружения
    db_name = os.getenv('DATABASE_NAME')
    db_user = os.getenv('DATABASE_USER')
    db_password = os.getenv('DATABASE_PASSWORD')
    db_host = os.getenv('DATABASE_HOST')
    db_port = os.getenv('DATABASE_PORT', '5432')

    # Создание имени файла для дампа базы данных
    dump_dir = './dumps'
    if not os.path.exists(dump_dir):
        os.makedirs(dump_dir)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    dump_file = f'{dump_dir}/dump_{timestamp}.sql'

    # Команда для создания дампа базы данных
    command = [
        'pg_dump',
        f'--dbname=postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}',
        '--file', dump_file
    ]

    # Выполнение команды создания дампа базы данных
    try:
        subprocess.run(command, check=True)
        print(f'Database dump created: {dump_file}')
    except subprocess.CalledProcessError as e:
        print(f'Error during database dump: {e}')


def job_collect_data():
    try:
        connection = psycopg2.connect(
            database=os.getenv('DATABASE_NAME'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            host=os.getenv('DATABASE_HOST'),
            port=os.getenv('DATABASE_PORT', '5432')
        )
        create_table_if_not_exists(connection)
        max_page = find_max_page(url=stock_url)
        all_urls_of_posts = collect_all_url_posts(1)
        get_info_with_out_phone_number(connection, urls_posts=all_urls_of_posts)
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if connection:
            connection.close()


def schedule_jobs():
    schedule.every().day.at("07:55").do(job_collect_data)
    schedule.every().day.at("08:05").do(dump_database)


def main():
    try:
        schedule_jobs()
        while True:
            schedule.run_pending()
            time.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
