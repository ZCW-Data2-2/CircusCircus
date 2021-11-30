from flask import *
from flask_login import current_user
from forum.models import *
from forum.shared_functions import generateLinkPath

subforum_blueprint = Blueprint('subforum', __name__)


@subforum_blueprint.route('/subforum')
def subforum():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return render_template('error.html', error="That subforum does not exist!")
    if current_user.is_authenticated:
        posts = Post.query.filter(Post.subforum_id == subforum_id).order_by(Post.id.desc()).limit(50)
    else:
        posts = Post.query.filter(Post.subforum_id == subforum_id, Post.private == False).order_by(
            Post.id.desc()).limit(50)
    if not subforum.path:
        subforum.path = generateLinkPath(subforum.id)

    subforums = Subforum.query.filter(Subforum.parent_id == subforum_id).all()
    return render_template("subforum.html", subforum=subforum, posts=posts, subforums=subforums, path=subforum.path)



