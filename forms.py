from wtforms import TextField, PasswordField, HiddenField, Form, FileField
from wtforms import validators
from flask_wtf.file import FileAllowed, FileRequired

#files .py in the project
from model import User


def fo_honeypot(form, field):
	if len(field.data) > 0:
		raise validators.ValidationError('this field should be empety')

class Register_user(Form):
	username = TextField('Username',[validators.Required('Username is requireded'),
								validators.Length(min=4,max=15,
									                       message='Intro a username with min %(min)d and %(max)d long')
								])
	password = PasswordField('Password',[validators.Required('Password is requireded'),
								validators.Length(min=4,max=15,
									                       message='Intro a password with min %(min)d and %(max)d long')
								,validators.EqualTo('confirm','password not must match')])
	confirm = PasswordField('Repeat password')

	imagen = FileField('Imagen profile', validators=[
        FileAllowed([ 'jpg','jpeg',' png',' gif'], 'Solo se permiten imágenes')
    ])

	honey_pot = HiddenField('',[fo_honeypot])

	def validate_username(self,field):
		username = field.data
		user = User.query.filter_by(username = username).first()
		if user is not None:
			raise validators.ValidationError(message='Is already registered')
	
class Login_user(Form):
	username = TextField('Username',[validators.Required('Username is requireded'),
								validators.Length(min=4,max=15,
									                       message='Intro a username with min %(min)d and %(max)d long')
								])
	password = PasswordField('Password',[validators.Required('Password is requireded'),
								validators.Length(min=4,max=15,
									                       message='Intro a password with min %(min)d and %(max)d long')])

class Profile(Form):
	url = TextField('Add you profile img', [validators.Required('Please, intro you img Profile')])

class Profile_updte(Form):

	username = TextField('Username',[validators.Required('Username is requireded'),
								validators.Length(min=4,max=15,
									                       message='Intro a username with min %(min)d and %(max)d long')])
	imagen = FileField('Imagen profile')

class Chat_post(Form):

	comment = TextField('')

