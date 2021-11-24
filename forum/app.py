from flask import Flask

app = Flask(__name__)
app.config.update(
    TESTING=True,
    DEBUG=True,
    SECRET_KEY=b'kristofer',
    SITE_NAME="CHYRP",
    SITE_DESCRIPTION="CHYRP Has You Reading Posts",
    SQLALCHEMY_DATABASE_URI='sqlite:////tmp/database.db',
    IMAGES_PATH=['images']
)
