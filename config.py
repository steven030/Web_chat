import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    SECRET_KEY = os.getenv("SECRET_KEY")

class Is_development(Config):

    PORT = os.getenv("PORT", 5000)
    DEBUG = os.getenv("DEBUG", "False") == "True"

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
