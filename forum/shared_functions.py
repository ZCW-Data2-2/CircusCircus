from forum.models import *

def email_taken(email):
    return User.query.filter(User.email == email).first()