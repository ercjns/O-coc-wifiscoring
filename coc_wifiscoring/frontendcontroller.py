from flask import Blueprint, request, abort, render_template

from .models import db, Result

frontend = Blueprint("frontend", __name__)

@frontend.route('/')
def home():
    return render_template('COCwifihome.html')
    
@frontend.route('/results/<cclass>')
def cclass_results(cclass):
    q = Result.query.filter_by(cclassshort=cclass).all()
    return render_template('resulttable.html', cclass=cclass, items=q)