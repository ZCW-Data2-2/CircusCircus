from flask import Flask

app = Flask(__name__)
app.config.update(
    TESTING=True,
    DEBUG=True,
    SECRET_KEY=b'kristofer',
    SQLALCHEMY_DATABASE_URI='sqlite:///tmp/database.db',
    COPY_RIGHT="Copyright © 2021 CHYRP. All rights reserved",
    SITE_NAME="CHYRP",
    SITE_DESCRIPTION="CHYRP Has You Reading Posts",
    IMAGES_PATH=['images']
)
