# library from python3
from flask import request, render_template, url_for, Flask, session, redirect, flash
from flask_socketio import SocketIO, send, join_room
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import os

from imagekitio import ImageKit

from config import Is_delovepment
from model import User, db, CommentUser
import forms

# app flask
app = Flask(__name__)
app.config.from_object(Is_delovepment)

imagekit = ImageKit(
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
)

socketio = SocketIO(app, async_mode='threading')

db.init_app(app)

with app.app_context():
    db.create_all()


# -------------------------
# AUTH MIDDLEWARE
# -------------------------
@app.before_request
def before_request():
    if 'username' not in session and request.endpoint in [
        'chat_user', 'profile', 'loggout', 'profile_update'
    ]:
        return redirect(url_for('index'))

    elif 'username' in session and request.endpoint in [
        'login', 'register'
    ]:
        return redirect(url_for('index'))


# -------------------------
# INDEX
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    username = session['username'] if 'username' in session else None
    return render_template('index.html', title='Hi!', username=username)


# -------------------------
# REGISTER
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = forms.Register_user(request.form, request.files)

    if request.method == 'POST' and register_form.validate():

        user = User(
            register_form.username.data,
            register_form.password.data
        )

        image_file = request.files.get('imagen')

        if image_file and image_file.filename:

            filename = secure_filename(
                register_form.username.data + "_" + image_file.filename
            )

            image_bytes = image_file.read()

            # VALIDACIÓN REAL DE IMAGEN
            try:
                Image.open(BytesIO(image_bytes)).verify()
            except Exception:
                flash("Archivo de imagen inválido")
                return redirect(url_for('register'))

            try:
                upload = imagekit.upload(
                    file=image_bytes,
                    file_name=filename,
                    options={"use_unique_file_name": False}
                )

                user.image = upload.url

            except Exception:
                endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT").rstrip('/')
                user.image = f"{endpoint}/{filename}"

        else:
            user.image = "https://ik.imagekit.io/wannab1/default.png"

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('register.html', form=register_form)


# -------------------------
# LOGIN
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = forms.Login_user(request.form)

    if request.method == 'POST':

        user = User.query.filter_by(
            username=login_form.username.data
        ).first()

        if user and user.verify_password(login_form.password.data):

            session['username'] = user.username
            session['user_id'] = user.id
            session['user_img'] = user.image

            flash('Login successful')
            return redirect(url_for('index'))

        flash('Username or password incorrect')

    return render_template('login.html', form=login_form, title='Hi!')


# -------------------------
# LOGOUT
# -------------------------
@app.route('/loggout')
def loggout():
    session.clear()
    return redirect(url_for('index'))


# -------------------------
# CHAT
# -------------------------
@app.route('/chat_user', methods=['GET', 'POST'])
def chat_user():
    per_page = 20
    form_chat = forms.Chat_post(request.form)

    if 'username' in session:

        page = 1
        longitud = CommentUser.query.count()

        commentList = CommentUser.query.join(User).add_columns(
            User.username,
            User.image,
            CommentUser.text
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return render_template(
            'Chat__user.html',
            username=session['username'],
            img=session['user_img'],
            history=commentList,
            form=form_chat,
            log=longitud
        )

    return redirect(url_for('index'))


# -------------------------
# PROFILE
# -------------------------
@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('index'))

    return render_template(
        'profile_user.html',
        url_img=session.get('user_img'),
        username=session.get('username')
    )


# -------------------------
# PROFILE UPDATE
# -------------------------
@app.route('/profile_update', methods=['GET', 'POST'])
def profile_update():

    if 'username' not in session:
        return redirect(url_for('index'))

    update_form = forms.Profile_updte(request.form, request.files)

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST' and update_form.validate():

        image_file = request.files.get('imagen')

        # actualizar username siempre
        user.username = update_form.username.data

        if image_file and image_file.filename:

            filename = secure_filename(
                update_form.username.data + "_" + image_file.filename
            )

            image_bytes = image_file.read()

            # validar imagen
            try:
                Image.open(BytesIO(image_bytes)).verify()
            except Exception:
                flash("Imagen inválida")
                return redirect(url_for('profile_update'))

            try:
                upload = imagekit.upload(
                    file=image_bytes,
                    file_name=filename,
                    options={"use_unique_file_name": False}
                )

                user.image = upload.url

            except Exception:
                endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT").rstrip('/')
                user.image = f"{endpoint}/{filename}"

        db.session.commit()

        session['username'] = user.username
        session['user_img'] = user.image

        return redirect(url_for('profile'))

    return render_template('profile_updat.html', form=update_form)


# -------------------------
# SOCKET IO
# -------------------------
@socketio.on('message')
def handle_messages(msg):

    if msg and msg.strip():

        username = session.get('username')
        image = session.get('user_img')

        user = User.query.filter_by(username=username).first()

        if user:

            comment = CommentUser(
                user_id=user.id,
                text=msg
            )

            db.session.add(comment)
            db.session.commit()

            send({
                'username': username,
                'message': msg,
                'img': image,
                'alert': 'false'
            }, broadcast=True)


@socketio.on('connect')
def connect_user():

    if 'username' not in session:
        return False

    join_room(0)

    send({
        'username': session['username'],
        'message': ' has join the chat.',
        'alert': 'true'
    })


# -------------------------
if __name__ == '__main__':
    socketio.run(app, debug=True)
