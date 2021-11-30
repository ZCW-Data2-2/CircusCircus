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
from .shared_functions import email_taken, valid_title, valid_content, valid_password, valid_username, username_taken
from forum.profile.profile_blueprint import profile_blueprint, update_profile_blueprint, default_profile_blueprint


socketio = SocketIO(app)
images = Images(app)
db = SQLAlchemy(app)



#Blueprints
app.register_blueprint(profile_blueprint)
app.register_blueprint(update_profile_blueprint)
app.register_blueprint(default_profile_blueprint)


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




@app.route('/subforum')
def subforum():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")
    if current_user.is_authenticated:
        posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
    else:
        posts = Post.query.filter(Post.subforum_id == subforum_id, Post.private == False).order_by(
            Post.id.desc()).limit(50)
    if not subforum.path:
        subforum.path = generateLinkPath(subforum.id)

    subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
    return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforum.path)


@app.route('/loginform')
def loginform():
    return render_template("login.html")


# @login_required
@app.route('/addpost')
def addpost():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return error("That subforum does not exist!")

    return render_template("createpost.html", subforum=subforum)


@app.route('/viewpost')
def viewpost():
    postid = int(request.args.get("post"))
    post = Post.query.filter(Post.id == postid).first()
    if post.private:
        if not current_user.is_authenticated:
            return render_template("login.html", alert="login to view private posts")
    if not post:
        return render_template('error.html', error=f"Post with id {postid} does not exist.")
    if not post.subforum.path:
        subforum.path = generateLinkPath(post.subforum.id)
    comments = Comment.query.filter(Comment.post_id == postid).order_by(
        Comment.id.desc())  # no need for scalability now
    return render_template("viewpost.html", post=post, path=subforum.path, comments=comments)


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
@app.route('/action_post', methods=['POST'])
def action_post():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return redirect(url_for("subforums"))

    user = current_user
    title = request.form['title']
    content = request.form['content']
    url = request.form['url']
    image = request.form['image']
    private = False
    if request.form.get('private', False):
        private = True

    # check for valid posting
    errors = []
    retry = False
    if not valid_title(title):
        errors.append("Title must be between 4 and 140 characters long!")
        retry = True
    if not valid_content(content):
        errors.append("Post must be between 10 and 5000 characters long!")
        retry = True
    if retry:
        return render_template("createpost.html", subforum=subforum, errors=errors)

    post = Post(title, content, datetime.datetime.now(), private, url, image)
    # if request.method == 'POST':
    #     return request.form.getlist(private)

    subforum.posts.append(post)
    user.posts.append(post)
    db.session.commit()

    return redirect("/viewpost?post=" + str(post.id))


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


def generateLinkPath(subforumid):
    links = []
    subforum = Subforum.query.filter(Subforum.id == subforumid).first()
    parent = Subforum.query.filter(Subforum.id == subforum.parent_id).first()
    links.append("<a href=\"/subforum?sub=" + str(subforum.id) + "\">" + subforum.title + "</a>")
    while parent is not None:
        links.append("<a href=\"/subforum?sub=" + str(parent.id) + "\">" + parent.title + "</a>")
        parent = Subforum.query.filter(Subforum.id == parent.parent_id).first()
    links.append("<a href=\"/\">Forum Index</a>")
    link = ""
    for l in reversed(links):
        link = link + " / " + l
    return link


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
