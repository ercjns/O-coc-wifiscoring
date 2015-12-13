from flask import Flask

from .models import db
from .controller import telemetry

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)

app.register_blueprint(telemetry, url_prefix='/telemetry')