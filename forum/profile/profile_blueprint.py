import os
from flask import *
from flask_login import current_user
from forum.models import *
from forum.shared_functions import email_taken

profile_blueprint = Blueprint('profile_blueprint', __name__)
update_profile_blueprint = Blueprint('update_profile_blueprint', __name__)
default_profile_blueprint = Blueprint('default_profile_blueprint', __name__)


@default_profile_blueprint.route('/profile')
def profile_default():
    if current_user.is_authenticated:
        return redirect(f'/profile/{current_user.username}')
    else:
        return render_template("login.html", alert="login to edit your profile")


@profile_blueprint.route('/profile/<user_name>')
def profile(user_name):
    user = User.query.filter(User.username == user_name).first()
    owns_profile = False
    if not user:
        return render_template('error.html', error="user does not exist")
    if current_user.is_authenticated:
        if current_user.username == user_name:
            owns_profile = True
        recent_posts = Post.query.filter(Post.user_id == user.id).order_by(Post.id.desc()).limit(5)
        recent_comments = Comment.query.filter(Comment.user_id == user.id).order_by(Comment.id.desc()).limit(5)
    else:
        recent_posts = Post.query.filter(Post.user_id == user.id, Post.private == False).order_by(
            Post.id.desc()).limit(5)
        recent_comments = Comment.query.filter(Comment.user_id == user.id).join(Post).filter(
            Post.private == False).order_by(Comment.id.desc()).limit(5)

    return render_template("profile.html", user=user, recent_comments=recent_comments, recent_posts=recent_posts,
                           owns_profile=owns_profile)


@update_profile_blueprint.route('/action_profile_update', methods=['POST'])
def action_profile():
    filename = False
    if not current_user.is_authenticated:
        return render_template('error.html', error="Not Logged in, Shouldn't be here")
    user = User.query.filter_by(username=current_user.username).first()
    if 'profile_pic' in request.files:
        profile_pic = request.files['profile_pic']
        if profile_pic.filename != "":
            file_extension = profile_pic.filename.split('.')[-1].lower()
            if file_extension in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}:
                filename = f"{current_user.username}.{file_extension}"
                profile_pic.save(os.path.join('.', 'forum', 'images', filename))
            else:
                return render_template('error.html', error="bad filetype")

    email = request.form.get('email')  # access the data inside
    if email != current_user.email:
        if email_taken(email):
            return render_template('error.html', error="An account already exists with this email!")
    if email:
        user.email = email
    if filename:
        user.picture = filename
    db.session.commit()
    return redirect('/profile')
