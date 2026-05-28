import os
from io import BytesIO
from flask import Flask, request, render_template, url_for, session, redirect, flash
from flask_socketio import SocketIO, send
from werkzeug.utils import secure_filename
from PIL import Image
from imagekitio import ImageKit

from config import Is_delovepment
from model import User, db, CommentUser
import forms

app = Flask(__name__)
app.config.from_object(Is_delovepment)

# INICIALIZACIÓN CORRECTA (SDK v5.5.2+)
imagekit = ImageKit(private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"))

socketio = SocketIO(app, async_mode='threading')
db.init_app(app)

with app.app_context():
    db.create_all()

# ... (tus rutas before_request e index se mantienen igual) ...

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = forms.Register_user(request.form, request.files)
    if request.method == 'POST' and register_form.validate():
        if User.query.filter_by(username=register_form.username.data).first():
            flash("El nombre de usuario ya está registrado.")
            return render_template('register.html', form=register_form)

        user = User(register_form.username.data, register_form.password.data)
        image_file = request.files.get('imagen')

        if image_file and image_file.filename:
            filename = secure_filename(f"{register_form.username.data}_{image_file.filename}")
            try:
                img_data = Image.open(image_file.stream)
                buffer = BytesIO()
                img_data.save(buffer, format=img_data.format or 'JPEG')
                buffer.seek(0)
                
                # SUBIDA SIN 'options'
                upload_result = imagekit.files.upload(
                    file=buffer, 
                    file_name=filename, 
                    use_unique_file_name=False
                )
                
                if hasattr(upload_result, "url"):
                    user.image = upload_result.url
                else:
                    raise Exception("La API no devolvió una URL válida.")
                    
            except Exception as e:
                print(f"Error en subida: {e}")
                user.image = "https://ik.imagekit.io/wannab1/DEFAULT.png"
        else:
            user.image = "https://ik.imagekit.io/wannab1/DEFAULT.png"

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=register_form)

# ... (rutas login, loggout, chat_user y profile se mantienen igual) ...

@app.route('/profile_update', methods=['GET', 'POST'])
def profile_update():
    user = User.query.filter_by(username=session['username']).first()
    update_form = forms.Profile_updte(request.form, request.files) if request.method == 'POST' else forms.Profile_updte(obj=user)

    if request.method == 'POST' and update_form.validate():
        user.username = update_form.username.data
        image_file = request.files.get('imagen')

        if image_file and image_file.filename:
            filename = secure_filename(f"{user.username}_{image_file.filename}")
            try:
                img = Image.open(image_file.stream)
                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                buffer.seek(0)

                # SUBIDA SIN 'options'
                result = imagekit.files.upload(
                    file=buffer,
                    file_name=filename,
                    use_unique_file_name=False
                )

                if hasattr(result, "url"):
                    user.image = result.url
                else:
                    raise Exception("La API devolvió un resultado sin URL.")

            except Exception as e:
                print(f"Error en update: {e}")
                flash("Error al subir la imagen a ImageKit.")
                return render_template('profile_updat.html', form=update_form)

        db.session.commit()
        session['username'] = user.username
        session['user_img'] = user.image
        flash("Perfil actualizado correctamente.")
        return redirect(url_for('profile'))

    return render_template('profile_updat.html', form=update_form)

# ... (resto del archivo socketio y __main__ igual) ...
