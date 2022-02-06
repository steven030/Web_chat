from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

import datetime


db = SQLAlchemy()

class User(db.Model):

	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(20),unique=True)
	password = db.Column(db.String(255), nullable = False)
	image = db.Column(db.String(255),nullable=True)
	comments = db.relationship('CommentUser')
	create_date = db.Column(db.DateTime, default = datetime.datetime.now)


	def __init__(self,username,password):
		self.username = username
		self.password = self.create_password(password)

	def create_password(self, password):

		return generate_password_hash(password)

	def verify_password(self, password):

		return check_password_hash(self.password, password)
	def get_user(self):
		return id

class CommentUser(db.Model):

    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    text = db.Column(db.Text)