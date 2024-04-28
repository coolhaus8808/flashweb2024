
import logging
import pymysql
from flask import Flask #pip install flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
logging.basicConfig()
logger = logging.getLogger('pymysql')
logger.setLevel(logging.DEBUG)

# SQLAlchemy inicializálása
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/moodle_2.0'
db = SQLAlchemy(app)

from webapp import routes, models
