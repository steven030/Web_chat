import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-key")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IMPORTANTE: en serverless NO uses rutas locales fijas
    UPLOAD_FOLDER = "/tmp/uploads"


class DevelopmentConfig(Config):
    DEBUG = True
    PORT = 5000
