from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object('config')
socketio = SocketIO(app)

from .models import db
from .telemetrycontroller import telemetry
from .admincontroller import admin
from .resultscontroller import resultsAPI
from .frontendcontroller import frontend

db.init_app(app)

app.register_blueprint(telemetry, url_prefix='/telemetry')
app.register_blueprint(admin, url_prefix='/admin')
app.register_blueprint(resultsAPI, url_prefix='/api')
app.register_blueprint(frontend)
