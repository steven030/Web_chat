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
# Se usa únicamente la private_key como definimos en el test de Colab
imagekit = ImageKit(private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"))

socketio = SocketIO(app, async_mode='threading')
db.init_app(app)

with app.app_context():
    db.create_all()

@app.before_request
def before_request():
    protected_endpoints = ['chat_user', 'profile', 'loggout', 'profile_update']
    guest_endpoints = ['login', 'register']
    if 'username' not in session and request.endpoint in protected_endpoints:
        return redirect(url_for('index'))
    if 'username' in session and request.endpoint in guest_endpoints:
        return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Hi!', username=session.get('username'))

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
                
                # SUBIDA CORRECTA: Sin 'options'
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
                # Esto imprimirá el error real en los logs de Render
                print(f"--- ERROR DETALLADO DE IMAGEKIT ---")
                print(e)
                print(f"Tipo de error: {type(e)}")
                flash(f"Error al subir: {str(e)}") 
                return render_template('profile_updat.html', form=update_form)
        else:
            user.image = "https://ik.imagekit.io/wannab1/DEFAULT.png"

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=register_form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = forms.Login_user(request.form)
    if request.method == 'POST':
        user = User.query.filter_by(username=login_form.username.data).first()
        if user and user.verify_password(login_form.password.data):
            session['username'] = user.username
            session['user_img'] = user.image
            return redirect(url_for('index'))
    return render_template('login.html', form=login_form)

@app.route('/loggout')
def loggout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/chat_user', methods=['GET', 'POST'])
def chat_user():
    commentList = CommentUser.query.join(User).add_columns(User.username, User.image, CommentUser.text).paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    return render_template('Chat__user.html', username=session.get('username'), img=session.get('user_img'), history=commentList, form=forms.Chat_post(request.form))

@app.route('/profile')
def profile():
    return render_template('profile_user.html', url_img=session.get('user_img'), username=session.get('username'))

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

                # SUBIDA CORRECTA: Sin 'options'
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
                # Esto imprimirá el error real en los logs de Render
                print(f"--- ERROR DETALLADO DE IMAGEKIT ---")
                print(e)
                print(f"Tipo de error: {type(e)}")
                flash(f"Error al subir: {str(e)}") 
                return render_template('profile_updat.html', form=update_form)

        db.session.commit()
        session['username'] = user.username
        session['user_img'] = user.image
        flash("Perfil actualizado correctamente.")
        return redirect(url_for('profile'))

    return render_template('profile_updat.html', form=update_form)

@socketio.on('message')
def handle_messages(msg):
    if msg and msg.strip():
        user = User.query.filter_by(username=session.get('username')).first()
        if user:
            db.session.add(CommentUser(user_id=user.id, text=msg.strip()))
            db.session.commit()
            send({'username': session['username'], 'message': msg.strip(), 'img': session['user_img'], 'alert': 'false'}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
