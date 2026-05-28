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
    # Sincronizado con 'loggout' (con doble 'g') para evitar el error 500 de Jinja/Werkzeug
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
                
                # Solución definitiva al bug '__dict__': proces
