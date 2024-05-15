from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO


app = Flask(__name__)
app.config.from_object('webapp.config.Config')
socketio = SocketIO(app)
db = SQLAlchemy(app)
app.config['sozas'] = "fuszeres_vaj"

from webapp import routes, models