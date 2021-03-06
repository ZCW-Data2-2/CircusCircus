import os
from flask import *
from flask_login import current_user, login_user, logout_user
from flask_login.utils import login_required

from forum.app import app
from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin

import re
from flask_login.login_manager import LoginManager

from werkzeug.security import generate_password_hash, check_password_hash


import os 


from flask_images import *

from flask_socketio import SocketIO, join_room, leave_room, emit, send

from flask_session import Session
from forum.models import *
from .shared_functions import email_taken, add_subforum, valid_password, valid_username, username_taken
from forum.profile.profile_blueprint import profile_blueprint, update_profile_blueprint, default_profile_blueprint
from forum.subforums.subforums_blueprint import subforum_blueprint
from forum.post.posts_blueprint import addpost_blueprint, viewpost_blueprint, action_post_blueprint

socketio = SocketIO(app)
images = Images(app)

# Blueprints
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
        # room="Open Chat Room"
        # session['user'] = user
        # session['room'] = room
        ##return "chat"
        return render_template("session1.html")
    else:
        return render_template("login.html", alert="login to join open chat room")


@socketio.on('join', namespace='/chat')
def join(message):
    user = current_user.username
    # room="Open Chat Room"
    # join_room(room)
    emit('status', {'msg': user + ' has joined the chat'}, broadcast=True)


@socketio.on('text', namespace='/chat')
def text(message):
    user = current_user.username
    # room = "Open Chat Room"
    emit('message', {'msg': session.get('user') + ' : ' + str(message['msg'])}, broadcast=True)


@socketio.on('left', namespace='/chat')
def left(message):
    user = current_user.username
    #    room = "Open Chat Room"
    #    leave_room(room)
    #    session.clear()
    emit('status', {'msg': user + ' has left the room.'})


# @app.route('/chat',methods=['GET', 'POST'])
# def sessions():
#    if current_user.is_authenticated:
#        user = current_user
#        return render_template("session3.html", user=user)
#    else:
#        return render_template("login.html", alert="login to join open chat room")

# def messageReceived(methods=['GET', 'POST']):
#    print('message was received!!!')
#

# @socketio.on('chat message')
# def handle_my_custom_event(json, methods=['GET', 'POST']):
#    print('received my event: ' + str(json))
#    socketio.emit('msg', json, callback=messageReceived)
# return render_template("login.html")


if __name__ == '__main__':
    port = int(os.environ["PORT"])
    app.run(host='0.0.0.0', port=port, debug=True)
    socketio.run(app, debug=True)
    # Session(app)


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


"""
# Account checks
def username_taken(username):
    return User.query.filter(User.username == username).first()


def email_taken(email):
    return User.query.filter(User.email == email).first()


def valid_username(username):
    if not username_regex.match(username):
        # username does not meet password reqirements
        return False
    # username is not taken and does meet the password requirements
    return True


def valid_password(password):
    return password_regex.match(password)


# Post checks
def valid_title(title):
    return len(title) > 4 and len(title) < 140


def valid_content(content):
    return len(content) > 10 and len(content) < 5000


# OBJECT MODELS


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password_hash = db.Column(db.Text)
    email = db.Column(db.Text)
    admin = db.Column(db.Boolean, default=False)
    posts = db.relationship("Post", backref="user")
    comments = db.relationship("Comment", backref="user")
    picture = db.Column(db.Text, default="icons/default_user.png")
    displayname = db.Column(db.Text)
    liked = db.relationship('Post_Like', foreign_keys='Post_Like.user_id', backref='user', lazy='dynamic')
    disliked = db.relationship('Post_Dislike', foreign_keys='Post_Dislike.user_id', backref='user', lazy='dynamic')

    def __init__(self, email, username, password, displayname):
        if not displayname:
            displayname = username
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.displayname = displayname

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = Post_Like(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            Post_Like.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return Post_Like.query.filter(
            Post_Like.user_id == self.id,
            Post_Like.post_id == post.id).count() > 0

    def dislike_post(self, post):
        if not self.has_disliked_post(post):
            dislike = Post_Dislike(user_id=self.id, post_id=post.id)
            db.session.add(dislike)

    def undislike_post(self, post):
        if self.has_disliked_post(post):
            Post_Dislike.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_disliked_post(self, post):
        return Post_Dislike.query.filter(
            Post_Dislike.user_id == self.id,
            Post_Dislike.post_id == post.id).count() > 0

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    comments = db.relationship("Comment", backref="post")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subforum_id = db.Column(db.Integer, db.ForeignKey('subforum.id'))
    postdate = db.Column(db.DateTime)
    private = db.Column(db.Boolean, default=False)
    url = db.Column(db.Text)
    image = db.Column(db.Text)



    likes = db.relationship("Post_Like", backref='post', lazy='dynamic')
    dislikes = db.relationship("Post_Dislike", backref='post', lazy='dynamic')


    # cache stuff
    lastcheck = None
    savedresponce = None



    def __init__(self, title, content, postdate, private, url, image):
        self.title = title
        self.content = content
        self.postdate = postdate
        self.private = private
        self.url = url
        self.image = image


    def get_time_string(self):
        # this only needs to be calculated every so often, not for every request
        # this can be a rudamentary chache
        now = datetime.datetime.now()
        if self.lastcheck is None or (now - self.lastcheck).total_seconds() > 30:
            self.lastcheck = now
        else:
            return self.savedresponce

        diff = now - self.postdate

        seconds = diff.total_seconds()
        print(seconds)
        if seconds / (60 * 60 * 24 * 30) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60 * 24 * 30))) + " months ago"
        elif seconds / (60 * 60 * 24) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60 * 24))) + " days ago"
        elif seconds / (60 * 60) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60))) + " hours ago"
        elif seconds / (60) > 1:
            self.savedresponce = " " + str(int(seconds / 60)) + " minutes ago"
        else:
            self.savedresponce = "Just a moment ago!"

        return self.savedresponce


class Subforum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text, unique=True)
    description = db.Column(db.Text)
    subforums = db.relationship("Subforum")
    parent_id = db.Column(db.Integer, db.ForeignKey('subforum.id'))
    posts = db.relationship("Post", backref="subforum")
    path = None
    hidden = db.Column(db.Boolean, default=False)

    def __init__(self, title, description):
        self.title = title
        self.description = description


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    postdate = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))

    lastcheck = None

    savedresponce = None

    def __init__(self, content, postdate):
        self.content = content
        self.postdate = postdate

    def get_time_string(self):
        # this only needs to be calculated every so often, not for every request
        # this can be a rudamentary chache
        now = datetime.datetime.now()
        if self.lastcheck is None or (now - self.lastcheck).total_seconds() > 30:
            self.lastcheck = now
        else:
            return self.savedresponce

        diff = now - self.postdate
        seconds = diff.total_seconds()
        if seconds / (60 * 60 * 24 * 30) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60 * 24 * 30))) + " months ago"
        elif seconds / (60 * 60 * 24) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60 * 24))) + " days ago"
        elif seconds / (60 * 60) > 1:
            self.savedresponce = " " + str(int(seconds / (60 * 60))) + " hours ago"
        elif seconds / (60) > 1:
            self.savedresponce = " " + str(int(seconds / 60)) + " minutes ago"
        else:
            self.savedresponce = "Just a moment ago!"
        return self.savedresponce


class Post_Like(db.Model):
    # __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Post_Dislike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))


"""
def init_site():
    admin = add_subforum("Forum", "Announcements, bug reports, and general discussion about the forum belongs here")
    add_subforum("Announcements", "View forum announcements here", admin)
    add_subforum("Bug Reports", "Report bugs with the forum here", admin)
    add_subforum("General Discussion", "Use this subforum to post anything you want")
    add_subforum("Other", "Discuss other things here")


def add_subforum(title, description, parent=None):
    sub = Subforum(title, description)
    if parent:
        for subforum in parent.subforums:
            if subforum.title == title:
                return
        parent.subforums.append(sub)
    else:
        subforums = Subforum.query.filter(Subforum.parent_id == None).all()
        for subforum in subforums:
            if subforum.title == title:
                return
        db.session.add(sub)
    print("adding " + title)
    db.session.commit()
    return sub


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


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