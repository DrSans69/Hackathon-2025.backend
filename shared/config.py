from dotenv import load_dotenv
import os

load_dotenv()

DEBUG = True

DB_NAME = "mydb"
DB_USER = "admin"
DB_PASS = "admin"
DB_HOST = "localhost"
DB_PORT = "5432"

DJANGO_SUPERUSER_USERNAME = "admin"
DJANGO_SUPERUSER_PASSWORD = "admin"
DJANGO_SUPERUSER_EMAIL = "john.doe@example.com"
