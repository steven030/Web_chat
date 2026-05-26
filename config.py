import os
from dotenv import load_dotenv

class Config(object):
	SECRET_KEY = os.urandom(20)
	IMAGES_UPLOADS = "/Users/macuser/Documents/webchat/Web_chat/static/source/uploads"


class Is_delovepment(Config):

	PORT = 5000
	DEBUG = True
	
	SQLALCHEMY_DATABASE_URI =  'mysql+pymysql://root:Feoleoas11_@localhost/webchat'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
