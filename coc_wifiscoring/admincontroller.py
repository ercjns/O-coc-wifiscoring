from flask import Blueprint, request, abort, render_template
from datetime import time
#Markup, redirect, url_for, abort

from .models import db, Club, Result, Entry, RemotePunch


admin = Blueprint("admin", __name__)

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
    
@admin.route('/finishers/club/<club>')
def club_finishers(club):
    q = Result.query.filter_by(clubshort=club).all()
    return render_template('basiclist.html', items=q)