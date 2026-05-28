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

imagekit = ImageKit(
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
)

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
    username = session.get('username')
    return render_template('index.html', title='Hi!', username=username)

@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = forms.Register_user(request.form, request.files)
    if request.method == 'POST' and register_form.validate():
        existing_user = User.query.filter_by(username=register_form.username.data).first()
        if existing_user:
            flash("El nombre de usuario ya está registrado.")
            return render_template('register.html', form=register_form)

        user = User(register_form.username.data, register_form.password.data)
        image_file = request.files.get('imagen')

        if image_file and image_file.filename:
            filename = secure_filename(f"{register_form.username.data}_{image_file.filename}")
            image_bytes = image_file.read()
            try:
                img_to_upload = Image.open(BytesIO(image_bytes))
                output_buffer = BytesIO()
                img_format = img_to_upload.format if img_to_upload.format else 'JPEG'
                img_to_upload.save(output_buffer, format=img_format)
                output_buffer.seek(0)
                
                upload = imagekit.upload(file=output_buffer, file_name=filename, options={"use_unique_file_name": False})
                
                url_oficial = None
                if hasattr(upload, "response_metadata"):
                    url_oficial = getattr(upload.response_metadata, "raw", {}).get("url")
                if not url_oficial and isinstance(upload, dict):
                    url_oficial = upload.get("url") or upload.get("response", {}).get("url")
                
                user.image = url_oficial if url_oficial else f"{os.getenv('IMAGEKIT_URL_ENDPOINT').rstrip('/')}/{filename}"
            except Exception as e:
                print(f"Error: {e}")
        else:
            user.image = "https://ik.imagekit.io/wannab1/default.png"

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
    form_chat = forms.Chat_post(request.form)
    page = request.args.get('page', 1, type=int)
    commentList = CommentUser.query.join(User).add_columns(User.username, User.image, CommentUser.text).paginate(page=page, per_page=20, error_out=False)
    return render_template('Chat__user.html', username=session.get('username'), img=session.get('user_img'), history=commentList, form=form_chat)

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
                img_to_upload = Image.open(BytesIO(image_file.read()))
                output_buffer = BytesIO()
                img_to_upload.save(output_buffer, format=img_to_upload.format or 'JPEG')
                output_buffer.seek(0)
                
                upload = imagekit.upload(file=output_buffer, file_name=filename, options={"use_unique_file_name": False})
                
                url_oficial = None
                if hasattr(upload, "response_metadata"):
                    url_oficial = getattr(upload.response_metadata, "raw", {}).get("url")
                if not url_oficial and isinstance(upload, dict):
                    url_oficial = upload.get
