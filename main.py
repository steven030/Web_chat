import os
from io import BytesIO
from flask import Flask, request, render_template, url_for, session, redirect, flash,jsonify
from flask_socketio import SocketIO, send, join_room, emit
from werkzeug.utils import secure_filename
from PIL import Image
from imagekitio import ImageKit


from config import Is_delovepment
from model import User, db, CommentUser, PrivateMessage 
import forms

app = Flask(__name__)
app.config.from_object(Is_delovepment)

# INICIALIZACIÓN (SDK v5.5.2+)
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
                print(f"--- ERROR REGISTRO: {e} ---")
                user.image = "https://ik.imagekit.io/wannab1/DEFAULT.png"
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
    # 1. Obtener lista de todos los usuarios para el panel izquierdo
    # Excluimos al usuario actual para no mostrarse a sí mismo
    users = User.query.filter(User.username != session.get('username')).all()
    
    # 2. Mantener la lógica de comentarios (opcional: puedes cambiar esto a PrivateMessage más adelante)
    commentList = CommentUser.query.join(User).add_columns(
        User.username, User.image, CommentUser.text
    ).paginate(page=request.args.get('page', 1, type=int), per_page=20, error_out=False)
    
    return render_template(
        'Chat__user.html', 
        username=session.get('username'), 
        img=session.get('user_img'), 
        history=commentList, 
        all_users=users,  # <--- Esta es la variable que tu HTML necesita
        form=forms.Chat_post(request.form)
    )

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
                # AQUÍ ESTABA EL ERROR: Usar 'img' y 'img.format'
                img = Image.open(image_file.stream)
                buffer = BytesIO()
                img.save(buffer, format=img.format or 'JPEG')
                buffer.seek(0)

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
                print(f"--- ERROR PROFILE_UPDATE: {e} ---")
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



@socketio.on('join_private')
def on_join_private():
    # Cada usuario se une a una sala con su ID al cargar la página
    user_id = User.query.filter_by(username=session.get('username')).first().id
    join_room(f"user_{user_id}")

@socketio.on('private_message')
def handle_private_message(data):
    sender = User.query.filter_by(username=session.get('username')).first()
    receiver_id = data['receiver_id']
    msg_text = data['message']

    new_msg = PrivateMessage(sender_id=sender.id, receiver_id=receiver_id, text=msg_text)
    db.session.add(new_msg)
    db.session.commit()

    # Enviamos al receptor Y TAMBIÉN al emisor para actualizar su propia pantalla
    payload = {
        'sender': sender.username, 
        'message': msg_text,
        'img': sender.image # <--- IMPORTANTE: incluir la imagen
    }
    
    emit('receive_private_message', payload, room=f"user_{receiver_id}")
    emit('receive_private_message', payload, room=f"user_{sender.id}") # Así el emisor también ve su mensaje


@app.route('/get_history/<int:receiver_id>')
def get_history(receiver_id):
    sender = User.query.filter_by(username=session['username']).first()
    # Recuperamos mensajes ordenados por fecha
    messages = PrivateMessage.query.filter(
        ((PrivateMessage.sender_id == sender.id) & (PrivateMessage.receiver_id == receiver_id)) |
        ((PrivateMessage.sender_id == receiver_id) & (PrivateMessage.receiver_id == sender.id))
    ).order_by(PrivateMessage.timestamp.asc()).all()
    
    # Obtenemos los datos necesarios
    data = []
    for m in messages:
        sender_user = User.query.get(m.sender_id)
        data.append({
            'sender': sender_user.username,
            'text': m.text,
            'img': sender_user.image,
            'is_me': (m.sender_id == sender.id)
        })
    return jsonify(data)



if __name__ == '__main__':
    socketio.run(app, debug=True)
