# Author: Prof. MM Ghassemi <ghassem3@msu.edu>
from flask import current_app as app, send_from_directory
from flask import render_template, redirect, request, session, url_for, copy_current_request_context
from flask_socketio import SocketIO, emit, join_room, leave_room, close_room, rooms, disconnect
from .utils.database.database  import database
from werkzeug.datastructures   import ImmutableMultiDict
from pprint import pprint
import json
import random
import functools
from . import socketio
db = database()

#######################################################################################
# AUTHENTICATION RELATED
#######################################################################################
def login_required(func):
    @functools.wraps(func)
    def secure_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login", next=request.url))
        return func(*args, **kwargs)
    return secure_function

# get user email
def getUser():
	return db.reversibleEncrypt('decrypt', session['email']) if 'email' in session else 'Unknown'

# validation
def user_required(id):
	email = getUser()
	boards = db.getAllBoards(email)
	print(boards)
	if boards.get('success'):
		if int(id) in boards.get('success')['id']:
			return True
	return False

# handle login
@app.route('/login')
def login():
	return render_template('login.html', user=getUser())

# handle logout
@app.route('/logout')
def logout():
	session.pop('email', default=None)
	return redirect('/')

# process login
@app.route('/processlogin', methods = ["POST","GET"])
def processlogin():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	email = form_fields['email']
	password = form_fields['password']
	status = db.authenticate(email, password)
	if status.get('success'):
		session['email'] = db.reversibleEncrypt('encrypt', form_fields['email'])
	return json.dumps(status)

# process sign up
@app.route('/processsignup', methods = ["POST","GET"])
def processsignup():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	email = form_fields['email']
	password = form_fields['password']
	status = db.createUser(email, password)
	if status.get('success'):
		session['email'] = db.reversibleEncrypt('encrypt', form_fields['email'])
	return json.dumps(status)


#######################################################################################
# CHATROOM RELATED
#######################################################################################
# render chat
@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=getUser())

# handle joined event
@socketio.on('joined', namespace='/board')
def joined(message):
	board_id = session['board_id']
	id = session['board_id']
	join_room(f'board/{id}')
	user = getUser()
	emit('status', {
        'msg': f'{user} has entered the room.',
        'user': user  # Include user info in the message
    }, room=f'board/{board_id}')

# handle send_message event
@socketio.on('send_message', namespace='/board')
def handle_message(message):
	board_id = session['board_id']
	user = message.get('user')  # Get the sender's username
	msg_content = message.get('msg')  # Get the message content
	emit('status', {
        'msg': f"{user}: {msg_content}",
        'user': user
    }, room=f'board/{board_id}')

# delete a card
@socketio.on('delete_card', namespace='/board')
def handle_delete(data):
	card_id = data.get('card_id')
	board_id = session['board_id']
	status = db.deleteCard(card_id, board_id)
	if status.get('success'):
        # Notify all clients in the board's room
		emit('card_deleted', {'card_id': card_id}, room=f'board/{board_id}')
	else:
		emit('error', {'msg': 'Failed to delete the card.'})

# create a card
@socketio.on('create_card', namespace='/board')
def handle_create(data):
	board_id = session['board_id']
	list_id = data.get('list_id')
	name = data.get('name')
	description = data.get('description')
	status = db.createCard(board_id, list_id, name, description)
	if status.get('success'):
        # Notify all clients in the board's room
		emit('card_created', {'card_id': status['success'], 'list_id': list_id}, room=f'board/{board_id}')
	else:
		emit('error', {'msg': 'Failed to create the card.'})

# edit a card
@socketio.on('edit_card', namespace='/board')
def handle_edit(data):
	board_id = session['board_id']
	id = data.get('card_id')
	name = data.get('name')
	description = data.get('description')
	status = db.updateCard(id, name, description)
	if status.get('success'):
        # Notify all clients in the board's room
		emit('card_edited', {'card_id': id, 'name': name, 'description': description}, room=f'board/{board_id}')
	else:
		emit('error', {'msg': 'Failed to edit the card.'})

# locked column in edit mode
@socketio.on('locked_column', namespace='/board')
def handle_locked(data):
	board_id = session['board_id']
	column_id = data['column_id']
	emit('column_locked', {'column_id': column_id}, broadcast=True, include_self=False, room=f'board/{board_id}')

# unlock the column
@socketio.on('unlocked_column', namespace='/board')
def handle_unlocked(data):
	board_id = session['board_id']
	column_id = data['column_id']
	emit('column_unlocked', {'column_id': column_id}, broadcast=True, include_self=False, room=f'board/{board_id}')

# move a card
@socketio.on('move_card', namespace='/board')
def handle_move(data):
	board_id = session['board_id']
	card_id = data['card_id']
	position = data['position']
	new_id = data['list_id']
	old_pos = db.getPosition(card_id)
	old_id = db.getListId(card_id)
	if int(old_id) != int(new_id):
		status = db.movingCardDifferentList(board_id, new_id, card_id, position)
		db.updateList(board_id, old_id)
	else:
		if (int(position) < int(old_pos)):
			status = db.movingCardUp(board_id, new_id, card_id, position)
		else:
			status = db.movingCardDown(board_id, new_id, card_id, position)
	emit('move_card', {'list_id': new_id, 'card_id': card_id, 'position': position}, room=f'board/{board_id}')

#######################################################################################
# OTHER
#######################################################################################
# route to home
@app.route('/')
@login_required
def root():
	return redirect('/home')

# render home
@app.route('/home')
@login_required
def home():
	print(db.query('SELECT * FROM users'))
	return render_template('home.html', user=getUser())

# static directory
@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)

# handle after request
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# render board.html
@app.route('/board')
@login_required
def board():
	board_data = db.getAllBoards(getUser())
	pprint(board_data)
	return render_template('board.html', user=getUser(), data=board_data)

# render create.html
@app.route('/create')
@login_required
def create():
	return render_template('create.html', user=getUser())

# validation
@app.route('/validateemail', methods = ["POST","GET"])
def validateemail():
	email = request.args.get('email')
	status = db.checkUser(email)
	return json.dumps(status)

# create a board
@app.route('/processcreate', methods = ["POST","GET"])
def processcreate():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	key = json.loads(list(form_fields.keys())[0])
	status = db.createBoard(key['name'], key['email'])
	print(status)
	return json.dumps(status)

# render board using id
@app.route('/board/<id>')
@login_required
def open_board(id):
    # Here 'id' will be the value from the URL path
	status = user_required(id)
	print(status)
	if status is False:
		return redirect('/home')
	name = db.getBoardName(id)
	data = db.getBoardData(id)
	pprint(data)
	session['board_id'] = id
	return render_template('project.html', user=getUser(), name=name, data=data)

# process delete
@app.route('/processdelete', methods = ["POST","GET"])
def process_delete(id):
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	id = form_fields['id']
	board_id = session['board_id']
	status = db.deleteCard(id, board_id)
	return json.dumps(status)

# process edit
@app.route('/processedit', methods = ["POST","GET"])
def processedit():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	id = form_fields['id']
	name = form_fields['name']
	description = form_fields['description']
	status = db.updateCard(id, name, description)
	print(status)
	return json.dumps(status)

# process add
@app.route('/processadd', methods = ["POST","GET"])
def processadd():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	board_id = session['board_id']
	list_id = form_fields['list_id']
	name = form_fields['name']
	description = form_fields['description']
	status = db.createCard(board_id, list_id, name, description)
	return json.dumps(status)

# process moving
@app.route('/processmoving', methods = ["POST","GET"])
def processmoving():
	form_fields = dict((key, request.form.getlist(key)[0]) for key in list(request.form.keys()))
	board_id = session['board_id']
	new_id = form_fields['list_id']
	card_id = form_fields['card_id']
	position = form_fields['position']
	old_pos = db.getPosition(card_id)
	print("new position", position)
	print("new column: ", new_id)
	old_id = db.getListId(card_id)
	print(old_id)
	if int(old_id) != int(new_id):
		status = db.movingCardDifferentList(board_id, new_id, card_id, position)
		db.updateList(board_id, old_id)
	else:
		if (int(position) < int(old_pos)):
			status = db.movingCardUp(board_id, new_id, card_id, position)
		else:
			status = db.movingCardDown(board_id, new_id, card_id, position)
	return json.dumps(status)