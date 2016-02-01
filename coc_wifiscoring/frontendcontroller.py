from flask import Blueprint, request, abort, render_template

from .models import db, Result, RemotePunch

frontend = Blueprint("frontend", __name__)

@frontend.route('/')
def home():
    return render_template('COCwifihome.html')

@frontend.route('/results/<cclass>')
def cclass_results(cclass):
    if cclass in ['1', '3', '7', '8M', '8F', '8G'] or cclass in ['W1F', 'W1M', 'W2F', 'W2M', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M']:
        q = Result.query.filter_by(cclassshort=cclass).all()
        return render_template('resulttable.html', cclass=cclass, items=q)
    else:
        return '404: Not found. Unknown class specified in the url', 404

@frontend.route('/results/')
def all_results():
    q = Result.query.all()
    return render_template('allresults.html', items=q)

@frontend.route('/meetstats/')
def meet_stats():
    download_items = Result.query.all()
    download_sicards = [a.sicard for a in download_items]
    
    check_items = RemotePunch.query.filter_by(station=17).group_by(RemotePunch.sicard).order_by(RemotePunch.time).all()
    
    fin = len(download_sicards)
    checked = 0
    
    out_items = []
    for card in check_items:
        if card.sicard not in download_sicards:
            checked += 1
            out_items.append(card)
            continue

    checked += fin
    
    return render_template('meetstats.html', checked=checked, downloaded=len(download_sicards), out=checked-fin, items=out_items)