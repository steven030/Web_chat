from wtforms import StringField, PasswordField, HiddenField, Form, FileField
from wtforms import validators
from flask_wtf.file import FileAllowed

from model import User


def fo_honeypot(form, field):
    if len(field.data) > 0:
        raise validators.ValidationError('This field should be empty')


class Register_user(Form):

    username = StringField(
        'Username',
        [
            validators.DataRequired(message='Username is required'),
            validators.Length(
                min=4,
                max=15,
                message='Enter a username between %(min)d and %(max)d characters long'
            )
        ]
    )

    password = PasswordField(
        'Password',
        [
            validators.DataRequired(message='Password is required'),
            validators.Length(
                min=4,
                max=15,
                message='Enter a password between %(min)d and %(max)d characters long'
            ),
            validators.EqualTo('confirm', message='Passwords must match')
        ]
    )

    confirm = PasswordField('Repeat password')

    imagen = FileField(
        'Imagen profile',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only images are allowed')
        ]
    )

    honey_pot = HiddenField('', [fo_honeypot])

    def validate_username(self, field):
        username = field.data
        user = User.query.filter_by(username=username).first()

        if user is not None:
            raise validators.ValidationError('Username is already registered')


class Login_user(Form):

    username = StringField(
        'Username',
        [
            validators.DataRequired(message='Username is required'),
            validators.Length(
                min=4,
                max=15,
                message='Enter a username between %(min)d and %(max)d characters long'
            )
        ]
    )

    password = PasswordField(
        'Password',
        [
            validators.DataRequired(message='Password is required'),
            validators.Length(
                min=4,
                max=15,
                message='Enter a password between %(min)d and %(max)d characters long'
            )
        ]
    )


class Profile(Form):

    url = StringField(
        'Add your profile img',
        [
            validators.DataRequired(message='Please enter your profile image')
        ]
    )


class Profile_updte(Form):

    username = StringField(
        'Username',
        [
            validators.DataRequired(message='Username is required'),
            validators.Length(
                min=4,
                max=15,
                message='Enter a username between %(min)d and %(max)d characters long'
            )
        ]
    )

    imagen = FileField('Imagen profile')


class Chat_post(Form):

    comment = StringField('')