from forum.models import *
import re

# Account checks
def username_taken(username):
    return User.query.filter(User.username == username).first()


def valid_username(username):
    username_regex = re.compile("^[a-zA-Z0-9!@#%&]{4,40}$")
    if not username_regex.match(username):
        # username does not meet password reqirements
        return False
    # username is not taken and does meet the password requirements
    return True


def valid_password(password):
    password_regex = re.compile("^[a-zA-Z0-9!@#%&]{6,40}$")
    return password_regex.match(password)

def email_taken(email):
    return User.query.filter(User.email == email).first()

# Post checks
def valid_title(title):
    return len(title) >= 4 and len(title) <= 140


def valid_content(content):
    return len(content) >= 10 and len(content) <= 5000

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