import os
from flask import *
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required
import re
from flask_login.login_manager import LoginManager
from flask_images import *
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_session import Session
from forum.models import *
from .shared_functions import email_taken, add_subforum, valid_password, valid_username, username_taken
from forum.profile.profile_blueprint import profile_blueprint, update_profile_blueprint, default_profile_blueprint
from forum.subforums.subforums_blueprint import subforum_blueprint
from forum.post.posts_blueprint import addpost_blueprint, viewpost_blueprint, action_post_blueprint


socketio = SocketIO(app)
images = Images(app)



#Blueprints
app.register_blueprint(profile_blueprint)
app.register_blueprint(update_profile_blueprint)
app.register_blueprint(default_profile_blueprint)
app.register_blueprint(subforum_blueprint)
app.register_blueprint(addpost_blueprint)
app.register_blueprint(viewpost_blueprint)
app.register_blueprint(action_post_blueprint)

# VIEWS
@app.route('/')
def index():
    subforums = Subforum.query.filter(Subforum.parent_id == None).order_by(Subforum.id)
    return render_template("subforums.html", subforums=subforums)






@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if current_user.is_authenticated:
        user = current_user.username
        room = "Open Chat Room"
        session['user'] = user
        session['room'] = room
        ##return "chat"
        return render_template("session1.html", session=session)
    else:
        return render_template("login.html", alert="login to join open chat room")


@socketio.on('join', namespace='/chat')
def join(message):
    user = current_user.username
    room = "Open Chat Room"
    join_room(room)
    emit('status', {'msg': 'Keerthi' + ' has joined the chat'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    user = current_user.username
    room = "Open Chat Room"
    emit('message', {'msg': session.get('user') + ' : ' + str(message['msg'])}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    user = current_user.username
    room = "Open Chat Room"
    leave_room(room)
    session.clear()
    emit('status', {'msg': user + ' has left the room.'}, room=room)


# @app.route('/chat',methods=['GET', 'POST'])
# def sessions():
#    if current_user.is_authenticated:
#        user = current_user
#        return render_template("session.html", user=user)
#    else:
#        return render_template("login.html", alert="login to join open chat room")

# def messageReceived(methods=['GET', 'POST']):
#    print('message was received!!!')
#
# @socketio.on('my event')
# def handle_my_custom_event(json, methods=['GET', 'POST']):
#    print('received my event: ' + str(json))
#    socketio.emit('my response', json, callback=messageReceived)
# return render_template("login.html")





if __name__ == '__main__':
    port = int(os.environ["PORT"])
    app.run(host='0.0.0.0', port=port, debug=True)
    socketio.run(app, debug=True)
    session = Session(app)






@app.route('/loginform')
def loginform():
    return render_template("login.html")



# ACTIONS

@login_required
@app.route('/action_comment', methods=['POST', 'GET'])
def comment():
    post_id = int(request.args.get("post"))
    post = Post.query.filter(Post.id == post_id).first()
    if not post:
        return error("That post does not exist!")
    content = request.form['content']
    postdate = datetime.datetime.now()
    comment = Comment(content, postdate)
    current_user.comments.append(comment)
    post.comments.append(comment)
    db.session.commit()
    return redirect("/viewpost?post=" + str(post_id))




# @login_required
@app.route('/action_like/<int:post_id>/<action>')
# @app.route('/action_like/<int:post_id>/<action>', methods=['POST', 'GET'])
def action_like(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'like':
        current_user.like_post(post)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_post(post)
        db.session.commit()
    return redirect(request.referrer)


@login_required
@app.route('/action_dislike/<int:post_id>/<action>')
# @app.route('/action_like/<int:post_id>/<action>', methods=['POST', 'GET'])
def action_dislike(post_id, action):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if action == 'dislike':
        current_user.dislike_post(post)
        db.session.commit()
    if action == 'undislike':
        current_user.undislike_post(post)
        db.session.commit()
    return redirect(request.referrer)


@app.route('/action_login', methods=['POST'])
def action_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter(User.username == username).first()
    if user and user.check_password(password):
        login_user(user)
    else:
        errors = []
        errors.append("Username or password is incorrect!")
        return render_template("login.html", errors=errors)
    return redirect("/")


@login_required
@app.route('/action_logout')
def action_logout():
    # todo
    logout_user()
    return redirect("/")


@app.route('/action_createaccount', methods=['POST'])
def action_createaccount():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    displayname = request.form['displayname']
    errors = []
    retry = False
    if username_taken(username):
        errors.append("Username is already taken!")
        retry = True
    if email_taken(email):
        errors.append("An account already exists with this email!")
        retry = True
    if not valid_username(username):
        errors.append("Username is not valid!")
        retry = True
    if not valid_password(password):
        errors.append("Password is not valid!")
        retry = True
    if retry:
        return render_template("login.html", errors=errors)
    user = User(email, username, password, displayname)
    if user.username == "admin":
        user.admin = True
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect("/")


def error(errormessage):
    return "<b style=\"color: red;\">" + errormessage + "</b>"





# from forum.app import db, app


login_manager = LoginManager()
login_manager.init_app(app)


# if __name__ == "__main__":
# 	#runsetup()
# 	port = int(os.environ["PORT"])
# 	app.run(host='0.0.0.0', port=port, debug=True)


# DATABASE STUFF
@login_manager.user_loader
def load_user(userid):
    return User.query.get(userid)


password_regex = re.compile("^[a-zA-Z0-9!@#%&]{6,40}$")
username_regex = re.compile("^[a-zA-Z0-9!@#%&]{4,40}$")



# def email_taken(email):
#     return User.query.filter(User.email == email).first()





# OBJECT MODELS NOW MOVED


"""
def interpret_site_value(subforumstr):
	segments = subforumstr.split(':')
	identifier = segments[0]
	description = segments[1]
	parents = []
	hasparents = False
	while('.' in identifier):
		hasparents = True
		dotindex = identifier.index('.')
		parents.append(identifier[0:dotindex])
		identifier = identifier[dotindex + 1:]
	if hasparents:
		directparent = subforum_from_parent_array(parents)
		if directparent is None:
			print(identifier + " could not find parents")
		else:
			add_subforum(identifier, description, directparent)
	else:
		add_subforum(identifier, description)

def subforum_from_parent_array(parents):
	subforums = Subforum.query.filter(Subforum.parent_id == None).all()
	top_parent = parents[0]
	parents = parents[1::]
	for subforum in subforums:
		if subforum.title == top_parent:
			cur = subforum
			for parent in parents:
				for child in subforum.subforums:
					if child.title == parent:
						cur = child
			return cur
	return None


def setup():
	siteconfig = open('./config/subforums', 'r')
	for value in siteconfig:
		interpret_site_value(value)
"""


def init_site():
    admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here")
    add_subforum("Announcements", "View forum announcements here", admin)
    add_subforum("Bug Reports", "Report bugs with the forum here", admin)
    add_subforum("General Discussion", "Use this subforum to post anything you want")
    add_subforum("Other", "Discuss other things here")


if not Subforum.query.all():
    init_site()
