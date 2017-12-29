from flask import Blueprint, request, abort, render_template, redirect, url_for, Response
from datetime import datetime
from functools import wraps
#Markup, redirect, url_for, abort
import ETL as ETL
from os.path import join

from .models import *
from . import app


admin = Blueprint("admin", __name__)

RenderConfig = {}
RenderConfig['BrandLarge'] = 'COC-logo-diamond-red-large.png'

## basic auth from http://flask.pocoo.org/snippets/8/
def check_auth(username, password):
    # return username == 'admin' and password == 'c0c'
    return username == app.config['ADMIN_USER'] and password == app.config['ADMIN_PASS']

def authenticate():
    return Response('Login Required', 401, 
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def auth_req(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@admin.route('/')
@auth_req
def hello():
    admin_events_url = url_for('admin.events')
    return '<html><a href="'+admin_events_url+'">Admin Events</a></html>'

@admin.route('/events', methods=['GET'])
@auth_req
def events():
    data = []
    events = Event.query.all()
    for e in events:
        versions = Version.query.filter_by(event=e.event_code).all()
        data.append((e, versions))
    return render_template('admin/events.html', data=data,
                                                config=RenderConfig)

@admin.route('/events/new', methods=['POST'])
@auth_req
def new_event():
    name = request.form['event-name']
    date = request.form['event-date']
    datetxt = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
    venue = request.form['event-venue']
    desc = request.form['event-description']
    event_type = request.form['event-type']

    events = Event.query.all()
    if len(events) == 0:
        code = date+'-1'
    else:
        for e in events:
            todaysevents = []
            if e.event_code.startswith(date):
                num = int(e.event_code.rsplit('-', 1)[1])
                todaysevents.append(num)
            if len(todaysevents) > 0:
                code = date+'-'+str(max(todaysevents)+1)
            else:
                code = date+'-1'

    newEvent = Event(code, name, datetxt, venue, desc)
    db.session.add(newEvent)
    db.session.commit()

    if event_type == 'wiol':
        with open(join('coc_wifiscoring', 'static', 'WIOLclassinfo.csv')) as f:
            wiolClasses = ETL.classCSV(f)
            for c in wiolClasses:
                new_class = EventClass(code, c)
                db.session.add(new_class)
            db.session.commit()
    elif event_type == 'basic':
        with open(join('coc_wifiscoring', 'static', 'Basicclassinfo.csv')) as f:
            basicClasses = ETL.classCSV(f)
            for c in basicClasses:
                new_class = EventClass(code, c)
                db.session.add(new_class)
            db.session.commit()
    elif event_type == 'ult':
        with open(join('coc_wifiscoring', 'static', 'UltimateOclassinfo.csv')) as f:
            ultClasses = ETL.classCSV(f)
            for c in ultClasses:
                new_class = EventClass(code, c)
                db.session.add(new_class)
            db.session.commit()
    else:
        #TODO: actually handle errors
        print("Unknown event type: {}".format(event_type))

    return redirect(url_for('admin.events'))

@admin.route('/events/rm/<id>', methods=['POST'])
@auth_req
def del_event(id):
    e = Event.query.get(id)
    code = e.event_code
    ec = EventClass.query.filter_by(event=code).delete()
    db.session.commit()
    r = Result.query.filter_by(event=code).delete()
    db.session.commit()
    tr = TeamResult.query.filter_by(event=code).delete()
    db.session.commit()
    v = Version.query.filter_by(event=code).delete()
    db.session.commit()
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for('admin.events'))


    
@admin.route('/finishers/club/<club>')
def club_finishers(club):
    q = Result.query.filter_by(clubshort=club).all()
    return render_template('basiclist.html', items=q)