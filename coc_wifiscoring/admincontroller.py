from flask import Blueprint, request, abort, render_template, redirect, url_for
from datetime import datetime
#Markup, redirect, url_for, abort
import ETL as ETL

from .models import *


admin = Blueprint("admin", __name__)

RenderConfig = {}
RenderConfig['BrandLarge'] = 'COC-logo-diamond-red-large.png'

#ToDo: SERVER admin view:
# block with a password
# allow to query, create, and edit database entries via gui:
# clean out everything
# create new orgs
# mock incoming telemetry data
# the possibilities are endless!


        
@admin.route('/')
def hello():
    return 'Hello administration world!'

@admin.route('/events', methods=['GET'])
def events():
    data = []
    events = Event.query.all()
    for e in events:
        versions = Version.query.filter_by(event=e.event_code).all()
        data.append((e, versions))
    return render_template('admin/events.html', data=data,
                                                config=RenderConfig)

@admin.route('/events/new', methods=['POST'])
def new_event():
    name = request.form['event-name']
    date = request.form['event-date']
    datetxt = datetime.strptime(date, '%Y-%m-%d').strftime('%d %B %Y')
    venue = request.form['event-venue']
    desc = request.form['event-description']

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

    wiolClasses = ETL.classCSV('WIOLclassinfo.csv')
    for c in wiolClasses:
        new_class = EventClass(code, c)
        db.session.add(new_class)
    db.session.commit()

    return redirect(url_for('admin.events'))

@admin.route('/events/rm/<id>', methods=['POST'])
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