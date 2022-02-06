#library from python3
from flask import request, render_template, url_for, Flask, session, redirect
from flask_socketio import SocketIO, send, join_room, leave_room
import socketio
from flask import flash
from PIL import Image
from werkzeug.utils import secure_filename
import os
from os import remove


#file .py inside proyect
from config import Is_delovepment
from model import User, db, CommentUser
import forms

 #list of users
list_users = []
commentList = []
sendm = False

#app flask
app = Flask(__name__)
app.config.from_object(Is_delovepment)
socketio = SocketIO(app)

@app.before_request
def before_request():
	if 'username' not in session and request.endpoint in ['chat_user','profile','loggout','profile_update']:
		return redirect(url_for('index'))
	elif 'username' in session and request.endpoint in ['login','register']:
		return redirect(url_for('index'))
@app.route('/', methods=['GET', 'POST'])
def index():
	title = 'Hi!'

	if 'username' in session:
		username = session['username']


										
	else: 

		username = None

	return render_template('index.html', title = title, username = username)

@app.route('/register', methods=['GET','POST'])
def register():
	title = 'LOAD CODE'

	register_form = forms.Register_user(request.form)

	if request.method == 'POST' and register_form.validate():

		user = User(register_form.username.data,
			        register_form.password.data)
		if request.files:
			images = request.files['image'];

			if images:
				images.filename = register_form.username.data+"_"+images.filename
				user.image = images.filename
				images.save(os.path.join(app.config['IMAGES_UPLOADS'], images.filename))
				print("images saved:", images.filename)

			else:

				images = 'index.png'
				user.image = images

		
		
		 

		db.session.add(user)
		db.session.commit()

		

		return redirect(url_for('index'))



	return render_template('register.html', title = title, form = register_form)

@app.route('/login', methods=['GET', 'POST'])
def login():


	title = 'Hi!'
	login_form = forms.Login_user(request.form)

	user = User.query.filter_by(username = login_form.username.data).first()

	if user:

		if request.method == 'POST' and user.verify_password(login_form.password.data):

			session['username'] = user.username
			session['user_id'] = user.id
			session['user_img'] = user.image


			print(user.image)
			


			flash('se ha iniciado correctamente')
			return redirect(url_for('index'))

		elif request.method == 'POST':
			flash('Username or password is incorrect')

	elif request.method == 'POST':
		flash('Username not exist')

	return render_template('login.html', form = login_form, title = title)

@app.route('/loggout')
def loggout():
	if 'username' in session:
		session.pop('username')
		session.pop('user_id')
		session.pop('user_img')

		# session['username'] = None
		# session['user_id'] = None
		# session['user_img'] = None


	return redirect(url_for('index'))





@app.route('/chat_user', methods=['POST','GET'])
@app.route('/chat_user/<int:page>', methods=['POST','GET'])

def chat_user(page = 1, name = ''):

	
	title = 'Hi!'
	_sid = ''
	longitud = 0
	
	per_page = 20

	form_chat = forms.Chat_post(request.form)
	if 'username' in session:

		
		
		#cookies of user
		username = session['username']
		img = session['user_img']
		
		user_id = session['user_id']
		session['reply'] = name
	
		
		#chat history for users
		longitud = CommentUser.query.count()
		page = int(longitud/20)
		commentList= CommentUser.query.join(User).add_columns(User.username, User.image, CommentUser.text).paginate(page,longitud,False)
		print(longitud,'<<<<< Aqui')
		# if commentList:
		# 	longitud = len(commentList.items)
			
		# 	commentList = CommentUser.query.join(User).add_columns(User.username, User.image, CommentUser.text).paginate(page,longitud,False)

		

		
			
	else:
		username = None
		img = None

	return render_template('Chat__user.html', title = title, page = page, log = longitud, username = username, history = commentList, img = img ,form = form_chat)



@app.route('/profile', methods=['GET','POST'])
def profile():
	img_user = ' '
	title = 'Hi!'

	username = None
	if 'username' in session:

		username = session['username']

		img_user =session['user_img']

		

		



	else:
		return redirect(url_for('index'))

	return render_template('profile_user.html', title=title, url_img = img_user, username = username)

@app.route('/profile_update', methods=['POST','GET'])
def profile_update():

	title = 'Hi!'
	update_form = forms.Profile_updte(request.form)

	if 'username' in session:

		user = User.query.filter_by(username=session['username']).first()
		if request.method == 'POST' and update_form.validate():

			path = app.config['IMAGES_UPLOADS'] +'/'+ session['user_img']


			if request.files:
				remove(path)
				images = request.files['image'];
				images.filename = update_form.username.data+"_"+images.filename
				user.image = images.filename
				images.save(os.path.join(app.config['IMAGES_UPLOADS'], images.filename))
				print("images saved:", images.filename)


			db.session.query(User).filter( User.id == session['user_id'] ).update({
					User.username: update_form.username.data,
					User.image:images.filename
				}
				)
			db.session.commit()

			session['username'] = user.username
			session['user_img'] = images.filename


			return redirect(url_for('profile'))

	else:
		return redirect(url_for('index'))


	return render_template('profile_updat.html',title = title, form = update_form)


@socketio.on('message')
def handle_messages(msg):

	if(msg != None or msg != " "):
		sendm = True
		username = session['username']
		image = session['user_img']

		print('message:' + msg)
		

		user = User.query.filter_by(username = username).first()
		if user is not None:
			session['user_id'] = user.id
			user_id = session['user_id']
			comment1 = CommentUser(user_id = user_id , text = msg)

			reply = session['reply']
			db.session.add(comment1)
			db.session.commit()
			msg = {'username':session['username'],'message':msg, 'img':image, 'alert':'false'}
			print('\n \n {} \n \n'.format(msg))
			
			send(msg,broadcast=True)
	else:
		return false


@socketio.on('connect')
def connect_user():
 
	
	username = session['username']
	img = session['user_img']
	# list_users.append(request.sid)
	# print(list_users)
	room = 0;
	join_room(room)
	
	
	send({'username':username,'message':' has join the chat.','alert':'true'})

@socketio.on('username', namespace='/chat_user')
def resive_username(username):
	list_users = [{username:request.sid}]

	print(list_users)


		

if __name__ == '__main__':

	db.init_app(app)
	with app.app_context():
		db.create_all()

	socketio.run(app,host = '0.0.0.0')