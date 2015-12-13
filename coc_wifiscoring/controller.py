from flask import Blueprint, request, abort, render_template
from datetime import time
#Markup, redirect, url_for, abort

from .models import db, RemotePunch


telemetry = Blueprint("telemetry", __name__)

@telemetry.route('/<int:control>')
def get_punches(control):
    try:
        q = RemotePunch.query.filter_by(station=control).all()
        return render_template('basiclist.html', items=q)
    except:
        abort(404)

@telemetry.route('/<int:control>', methods=['POST'])
def record_punch(control):
    try:
        body = request.get_json(force=True) #read json without json mimetype in header
        h,m,s = body['time'].split(':',3)
        punch = RemotePunch(body['station'], body['SIcard'], time(int(h),int(m),int(s)))
        db.session.add(punch)
        db.session.commit()
        return str(punch), 200
    except:
        abort(500)
        
@telemetry.route('/')
def hello():
    return 'Hello telemetry world!'