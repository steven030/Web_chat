# library from python3
from flask import request, render_template, url_for, Flask, session, redirect, send_from_directory
from flask_socketio import SocketIO, send, join_room, leave_room
import socketio
from flask import flash
from PIL import Image
from werkzeug.utils import secure_filename
import os
from os import remove
from imagekitio import ImageKit
#from imagekitio.models.UploadOptions import UploadOptions
# file .py inside project
from config import Is_delovepment
from model import User, db, CommentUser
import forms

# list of users
list_users = []
commentList = []
sendm = False

# app flask
app = Flask(__name__)
app.config.from_object(Is_delovepment)

imagekit = ImageKit(
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
)

socketio = SocketIO(
    app,
    async_mode='threading'
)

print(os.getenv("DATABASE_URL"))

db.init_app(app)

with app.app_context():
    db.create_all()



class ImageKitOptions:
    def __init__(self, use_unique_file_name=False):
        self.use_unique_file_name = use_unique_file_name


@app.before_request
def before_request():
    if 'username' not in session and request.endpoint in ['chat_user', 'profile', 'loggout', 'profile_update']:
        return redirect(url_for('index'))
    elif 'username' in session and request.endpoint in ['login', 'register']:
        return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    title = 'Hi!'

    username = session['username'] if 'username' in session else None

    return render_template('index.html', title=title, username=username)


@app.route('/register', methods=['GET', 'POST'])
def register():
    title = 'LOAD CODE'
    # CORRECCIÓN: Se añade request.files
    register_form = forms.Register_user(request.form, request.files)

    if request.method == 'POST' and register_form.validate():

        user = User(register_form.username.data,
                    register_form.password.data)

        if request.files:
            images = request.files.get('imagen')

            if images and images.filename != '':
                filename = secure_filename(
                    register_form.username.data + "_" + images.filename
                )
            
                images.seek(0)
                image_bytes = images.read()
            
                # Instanciamos nuestro objeto casero compatible
                subida_opciones = ImageKitOptions(use_unique_file_name=False)
            
                try:
                    upload = imagekit.upload(
                        file=image_bytes,
                        file_name=filename,
                        options=subida_opciones # <--- El SDK leerá esto felizmente
                    )
                    user.image = upload.response_metadata.raw["url"]
                except TypeError as e:
                    if "description" in str(e):
                        endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT").rstrip('/')
                        user.image = f"{endpoint}/{filename}"
                    else:
                        raise e
            else:
                user.image = "https://ik.imagekit.io/wannab1/default.png"
                
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('register.html', title=title, form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    title = 'Hi!'
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

        else:
            flash('Username or password incorrect')

    return render_template('login.html', form=login_form, title=title)


@app.route('/loggout')
def loggout():
    if 'username' in session:
        session.pop('username')
        session.pop('user_id')
        session.pop('user_img')

    return redirect(url_for('index'))


@app.route('/chat_user', methods=['POST', 'GET'])
@app.route('/chat_user/<int:page>', methods=['POST', 'GET'])
def chat_user(page=1, name=''):

    title = 'Hi!'
    longitud = 0

    per_page = 20
    form_chat = forms.Chat_post(request.form)

    if 'username' in session:

        username = session['username']
        img = session['user_img']
        user_id = session['user_id']

        session['reply'] = name

        longitud = CommentUser.query.count()
        page = int(max(longitud / per_page, 1))

        commentList = CommentUser.query.join(User).add_columns(
            User.username,
            User.image,
            CommentUser.text
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    else:
        username = None
        img = None
        commentList = None

    return render_template(
        'Chat__user.html',
        title=title,
        page=page,
        log=longitud,
        username=username,
        history=commentList,
        img=img,
        form=form_chat
    )


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    title = 'Hi!'
    img_user = ''
    username = None

    if 'username' in session:
        username = session['username']
        img_user = session['user_img']
    else:
        return redirect(url_for('index'))

    return render_template(
        'profile_user.html',
        title=title,
        url_img=img_user,
        username=username
    )


@app.route('/profile_update', methods=['POST', 'GET'])
def profile_update():
    title = 'Hi!'
    update_form = forms.Profile_updte(request.form, request.files)

    if 'username' not in session:
        return redirect(url_for('index'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST' and update_form.validate():

        images = request.files.get('imagen')

        # actualizar username SIEMPRE
        user.username = update_form.username.data

        if images and images.filename != '':

            filename = secure_filename(
                update_form.username.data + "_" + images.filename
            )

            try:
                upload = imagekit.upload(
                    file=images.read(),
                    file_name=filename,
                    options={
                        "use_unique_file_name": False
                    }
                )

                # URL real de ImageKit
                user.image = upload.url

            except TypeError as e:
                if "description" in str(e):
                    endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT").rstrip('/')
                    user.image = f"{endpoint}/{filename}"
                else:
                    raise e

        # guardar cambios en DB
        db.session.commit()

        # sincronizar sesión
        session['username'] = user.username
        session['user_img'] = user.image

        return redirect(url_for('profile'))

    return render_template(
        'profile_updat.html',
        title=title,
        form=update_form
    )


@socketio.on('message')
def handle_messages(msg):

    if msg is not None and msg != " ":

        username = session['username']
        image = session['user_img']

        user = User.query.filter_by(username=username).first()

        if user is not None:
            session['user_id'] = user.id

            comment1 = CommentUser(
                user_id=session['user_id'],
                text=msg
            )

            db.session.add(comment1)
            db.session.commit()

            msg = {
                'username': username,
                'message': msg,
                'img': image,
                'alert': 'false'
            }

            send(msg, broadcast=True)

    else:
        return False


@socketio.on('connect')
def connect_user():

    if 'username' not in session:
        return False

    username = session['username']
    img = session.get('user_img')

    room = 0
    join_room(room)

    send({
        'username': username,
        'message': ' has join the chat.',
        'alert': 'true'
    })


@socketio.on('username', namespace='/chat_user')
def resive_username(username):
    list_users = [{username: request.sid}]
    print(list_users)


if __name__ == '__main__':
    socketio.run(app, debug=True)
