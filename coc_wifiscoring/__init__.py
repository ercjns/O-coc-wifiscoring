from flask import Flask
from flask_socketio import SocketIO

# app = Flask(__name__)
app = Flask(__name__, instance_relative_config=True)

app.config.from_object('config')
try:
    app.config.from_pyfile('instanceconfig.py')
except IOError:
    print('No Instane config')
    pass

socketio = SocketIO(app)

from .models import db
from .telemetrycontroller import telemetry
from .admincontroller import admin
from .apicontroller import API
from .frontendcontroller import frontend

db.init_app(app)

app.register_blueprint(telemetry, url_prefix='/telemetry')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(API, url_prefix='/api')
app.register_blueprint(frontend)
