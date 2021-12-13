from flask_login.utils import login_required
from forum.shared_functions import valid_title, valid_content
from flask import *
from flask_login import current_user
from forum.models import *
from forum.shared_functions import generateLinkPath

addpost_blueprint = Blueprint('addpost_blueprint', __name__)
viewpost_blueprint = Blueprint('viewpost_blueprint', __name__)
action_post_blueprint = Blueprint('action_post_blueprint', __name__)

@login_required
@addpost_blueprint.route('/addpost')
def addpost():
    subforum_id = int(request.args.get("sub"))
    subforum = Subforum.query.filter(Subforum.id == subforum_id).first()
    if not subforum:
        return render_template('error.html', error="That subforum does not exist!")

    return render_template("createpost.html", subforum=subforum)


@viewpost_blueprint.route('/viewpost')
def viewpost():
    postid = int(request.args.get("post"))
    post = Post.query.filter(Post.id == postid).first()
    if post.private:
        if not current_user.is_authenticated:
            return render_template("login.html", alert="login to view private posts")
    if not post:
        return render_template('error.html', error=f"Post with id {postid} does not exist.")
    if not post.subforum.path:
        path = generateLinkPath(post.subforum.id)
    comments = Comment.query.filter(Comment.post_id == postid).order_by(
        Comment.id.desc())  # no need for scalability now
    return render_template("viewpost.html", post=post, path=path, comments=comments)


@login_required
@action_post_blueprint.route('/action_post', methods=['POST'])
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
