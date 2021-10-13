import os
from datetime import timedelta

database_url = os.environ['AUTH_DATABASE_URL']


class Configuration:
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:root@{database_url}/authenticationDB'
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30, hours=1)

