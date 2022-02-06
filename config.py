import os
from dotenv import load_dotenv

class Config(object):
	SECRET_KEY = os.urandom(20)
	IMAGES_UPLOADS = "your path of the directory upload of this proyect"


class Is_delovepment(Config):

	PORT = 5000
	DEBUG = True
	
	SQLALCHEMY_DATABASE_URI =  'mysql+pymysql://your_mysql-server'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
