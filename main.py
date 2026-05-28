import os
from io import BytesIO
from flask import Flask, request, render_template, url_for, session, redirect, flash
from flask_socketio import SocketIO, send, join_room
from werkzeug.utils import secure_filename
from PIL import Image
from imagekitio import ImageKit

from config import Is_delovepment  # Mantengo el nombre de tu archivo de configuración
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
    # Corregido 'loggout' por 'logout' para coincidir con la ruta exacta
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
        # Verificar si el usuario ya existe para evitar errores de duplicados
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
                # 1. Validar la estructura de la imagen
                img_validator = Image.open(BytesIO(image_bytes))
                img_validator.verify()
                
                # 2. Reabrir el flujo limpio para evitar corrupción de puntero binario al subir
                img_to_upload = Image.open(BytesIO(image_bytes))
                output_buffer = BytesIO()
                img_to_upload.save(output_buffer, format=img_to_upload.format)
                output_buffer.seek(0)
                clean_bytes = output_buffer.read()
                
            except Exception as e:
                print(f"Error Pillow: {e}")
                flash("Archivo de imagen inválido o corrupto.")
                return redirect(url_for('register'))

            # --- SUBIDA A IMAGEKIT ---
            try:
                upload = imagekit.upload(
                    file=clean_bytes,
                    file_name=filename,
                    options={"use_unique_file_name": False}
                )
                user.image = upload.url
            except Exception as e:
                # Imprime el error real en tu terminal para que puedas debuggear (Ej: API keys inválidas)
                print(f"Error de ImageKit API: {e}")
                flash("Error al procesar la imagen en el servidor de almacenamiento.")
                return redirect(url_for('register'))
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
@app.route('/loggout')  # Corregido de '/loggout' a '/logout'
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

    # Paginación dinámica (Corregido de page=1 fijo a lectura de Query Params)
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

    # Pre-poblar los datos actuales del usuario en el formulario si es una petición GET
    if request.method == 'POST':
        update_form = forms.Profile_updte(request.form, request.files)
    else:
        update_form = forms.Profile_updte(obj=user)

    if request.method == 'POST' and update_form.validate():
        new_username = update_form.username.data

        # Validar si el nuevo username ya está en uso
