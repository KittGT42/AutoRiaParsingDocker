Create .env file:
Create a .env file in the root directory of the project and add the following environment variables:

env
Copy code
POSTGRES_DB=car_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123
DATABASE_HOST=db
DATABASE_NAME=car_data
DATABASE_USER=postgres
DATABASE_PASSWORD=123
SELENIUM_HOST=selenium
SELENIUM_PORT=4444
Build and run the Docker containers:

sh
Copy code
docker-compose up --build
Access pgAdmin:

Open your web browser and go to http://localhost:8080.
Login with the default credentials:
Email: admin@admin.com
Password: admin
Add a new server in pgAdmin:
Name: Car Data DB
Host: db
Port: 5432
Username: postgres
Password: 123
Directory Structure
app/: Contains the source code of the application.
dumps/: Directory where database dumps are stored.
Dockerfile: Dockerfile to build the application container.
docker-compose.yml: Docker Compose configuration file.
pyproject.toml: Poetry configuration file for managing dependencies.
poetry.lock: Poetry lock file.
Usage
The application will automatically start collecting data according to the schedule defined in the main1.py file. By default, it collects data daily at 19:00 and dumps the database at 19:15.

To manually trigger data collection or database dump, you can modify the schedule in main1.py.

Development
To set up the development environment:

Install Poetry:

sh
Copy code
pip install poetry
Install dependencies:

sh
Copy code
poetry install
Run the application:

sh
Copy code
poetry run python main1.py