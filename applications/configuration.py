import os
from datetime import timedelta

databaseUrl = os.getenv('VOTING_DATABASE_URL', 'localhost:3306')
redisUrl = os.getenv('REDIS_URL', 'localhost')


class Configuration:
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:root@{databaseUrl}/votingDB'
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    REDIS_HOST = redisUrl
    REDIS_VOTES_LIST = "votes"

