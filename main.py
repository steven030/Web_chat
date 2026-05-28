import os
from io import BytesIO
import base64  # Requerido para la conversión limpia a ImageKit
from flask import Flask, request, render_template, url_for, session, redirect, flash
from flask_socketio import SocketIO, send, join_room
from werkzeug.utils import secure_filename
from PIL import Image
from imagekitio import ImageKit

from config import Is_delovepment  
from model import User, db, CommentUser
import forms

# Inicialización de Flask
app = Flask(__name__)
app.config.from_object(Is_delovepment)

# Inicialización de ImageKit con variables de entorno
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
    protected_endpoints = ['chat_user', 'profile', 'loggout', 'profile_update']
    guest_endpoints = ['login', 'register']

    if 'username' not in session and request.endpoint in protected_endpoints:
        return redirect(url_for('index'))

    if 'username' in session and request.endpoint in guest_endpoints:
        return redirect(url_for('index'))


# -------------------------
# INDEX
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    username = session.get('username')
    return render_template('index.html', title='Hi!', username=username)


# -------------------------
# REGISTER
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = forms.Register_user(request.form, request.files)

    if request.method == 'POST' and register_form.validate():
        existing_user = User.query.filter_by(username=register_form.username.data).first()
        if existing_user:
            flash("El nombre de usuario ya está registrado.")
            return render_template('register.html', form=register_form)

        user = User(
            register_form.username.data,
            register_form.password.data
        )

        image_file = request.files.get('imagen')

        if image_file and image_file.filename:
            filename = secure_filename(f"{register_form.username.data}_{image_file.filename}")
            image_bytes = image_file.read()

            # --- PROCESAMIENTO Y VALIDACIÓN SEGURA DE IMAGEN ---
            try:
                img_validator = Image.open(BytesIO(image_bytes))
                img_validator.verify()
                
                img_to_upload = Image.open(BytesIO(image_bytes))
                output_buffer = BytesIO()
                img_to_upload.save(output_buffer, format=img_to_upload.format)
                output_buffer.seek(0)
                
                # Convertimos a Base64 string para una compatibilidad absoluta con ImageKit
                base64_img = base64.b64encode(output_buffer.read()).decode('utf-8')
                
            except Exception as e:
                print(f"Error Pillow: {e}")
                flash("Archivo de imagen inválido o corrupto.")
                return redirect(url_for('register'))

            # --- SUBIDA A IMAGEKIT ---
            try:
                upload = imagekit.upload(
                    file=base64_img,  # Enviamos el string codificado en Base64
                    file_name=filename,
                    options={"use_unique_file_name": False}
                )
                
                if isinstance(upload, dict):
                    user.image = upload.get("url") or upload.get("response", {}).get("url")
                else:
                    user.image = getattr(upload, "url", None)

                if not user.image:
                    raise ValueError("La respuesta de ImageKit no contiene una URL válida.")

            except Exception as e:
                print(f"Error de ImageKit API: {e}")
                endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT", "").rstrip('/')
                user.image = f"{endpoint}/{filename}"
        else:
            user.image = "https://ik.imagekit.io/wannab1/default.png"

        db.session.add(user)
        db.session.commit()
        flash("Usuario registrado con éxito.")
        return redirect(url_for('login'))

    return render_template('register.html', form=register_form)


# -------------------------
# LOGIN
# -------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = forms.Login_user(request.form)

    if request.method == 'POST':
        user = User.query.filter_by(username=login_form.username.data).first()

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

    page = request.args.get('page', 1, type=int)
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
        username=session.get('username'),
        img=session.get('user_img'),
        history=commentList,
        form=form_chat,
        log=longitud
    )


# -------------------------
# PROFILE
# -------------------------
@app.route('/profile')
def profile():
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
    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        update_form = forms.Profile_updte(request.form, request.files)
    else:
        update_form = forms.Profile_updte(obj=user)

    if request.method == 'POST' and update_form.validate():
        new_username = update_form.username.data

        if new_username != user.username:
            username_check = User.query.filter_by(username=new_username).first()
            if username_check:
                flash("Ese nombre de usuario ya está tomado.")
                return render_template('profile_updat.html', form=update_form)

        user.username = new_username
        image_file = request.files.get('imagen')

        if image_file and image_file.filename:
            filename = secure_filename(f"{new_username}_{image_file.filename}")
            image_bytes = image_file.read()

            # --- PROCESAMIENTO Y VALIDACIÓN SEGURA DE IMAGEN ---
            try:
                img_validator = Image.open(BytesIO(image_bytes))
                img_validator.verify()
                
                img_to_upload = Image.open(BytesIO(image_bytes))
                output_buffer = BytesIO()
                img_to_upload.save(output_buffer, format=img_to_upload.format)
                output_buffer.seek(0)
                
                # Convertimos a Base64 string para el update
                base64_img = base64.b64encode(output_buffer.read()).decode('utf-8')
            except Exception as e:
                print(f"Error Pillow en update: {e}")
                flash("Imagen inválida o corrupto.")
                return redirect(url_for('profile_update'))

            # --- SUBIDA A IMAGEKIT ---
            try:
                upload = imagekit.upload(
                    file=base64_img,  # Enviamos el string codificado en Base64
                    file_name=filename,
                    options={"use_unique_file_name": False}
                )
                
                if isinstance(upload, dict):
                    user.image = upload.get("url") or upload.get("response", {}).get("url")
                else:
                    user.image = getattr(upload, "url", None)

                if not user.image:
                    raise ValueError("La respuesta de ImageKit no contiene una URL válida.")

            except Exception as e:
                print(f"Error de ImageKit API en update: {e}")
                endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT", "").rstrip('/')
                user.image = f"{endpoint}/{filename}"

        db.session.commit()

        # Actualizar datos de la sesión activa
        session['username'] = user.username
        session['user_img'] = user.image

        flash("Perfil actualizado correctamente.")
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
                text=msg.strip()
            )

            db.session.add(comment)
            db.session.commit()

            send({
                'username': username,
                'message': msg.strip(),
                'img': image,  # Enviamos la URL absoluta directa de ImageKit
                'alert': 'false'
            }, broadcast=True)


@socketio.on('connect')
def connect_user():
    if 'username' not in session:
        return False

    send({
        'username': session['username'],
        'message': ' has joined the chat.',
        'alert': 'true'
    }, broadcast=True)


if __name__ == '__main__':
    socketio.run(app, debug=True)
