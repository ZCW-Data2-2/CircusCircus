from flask import Flask
import os

app = Flask(__name__)
app.config.update(
    TESTING=True,
    DEBUG=True,
    SECRET_KEY=b'kristofer',
    COPY_RIGHT="Copyright © 2021 CHYRP. All rights reserved",
    SITE_NAME="CHYRP",
    SITE_DESCRIPTION="CHYRP Has You Reading Posts",
    IMAGES_PATH=['images'],
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'],
    # SQLALCHEMY_DATABASE_URI='postgresql://ccuser:foobar@localhost/circuscircus',
    SQLALCHEMY_TRACK_MODIFICATIONS=True
)

