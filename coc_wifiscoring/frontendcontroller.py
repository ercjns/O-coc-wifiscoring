from flask import Blueprint, request, abort, render_template, redirect, url_for
from .models import *
import copy
from datetime import datetime


frontend = Blueprint("frontend", __name__)

RenderConfig = {}
RenderConfig['BrandLarge'] = 'COC-logo-diamond-red-large.png'
# RenderConfig['BrandLarge'] = 'armadillo.png'

WIOL_CLASSES = ['W1F', 'W1M', 'W2F', 'W2M', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M']
WIOL_TEAM_CLASSES = ['W2T', 'W3FT', 'W4MT', 'W5MT', 'W6FT', 'W6MT']

@frontend.route('/')
def home():
    events = Event.query.all()
    events.sort(key=lambda x: x.event_code)
    if len(events) == 1:
        event_code = events[0].event_code
        return redirect(url_for('frontend.event_class_select',
                                event_code=event_code))
    else:
        time = datetime.now()
        return render_template('COCwifihome.html',
                               config=RenderConfig,
                               events=events,
                               time=time)

@frontend.route('/event/<event_code>/')
def event_class_select(event_code):
    version = _getResultVersion(event_code)
    time = version.filetimestamp
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    event_classes = EventClass.query.filter_by(event=event_code).all()

    wiol = [c for c in event_classes if c.class_code in WIOL_CLASSES]
    wiolT = [c for c in event_classes if c.class_code in WIOL_TEAM_CLASSES]
    public = [c for c in event_classes if c not in wiol + wiolT]

    wiol.sort(key=lambda x: x.class_code)
    wiolT.sort(key=lambda x: x.class_code)
    public.sort(key=lambda x: x.class_code)

    return render_template('EventClassSelect.html', config=RenderConfig, 
                                                    time=time, 
                                                    event=event,
                                                    wiol=wiol, 
                                                    wiolT=wiolT,
                                                    public=public)

@frontend.route('/event/<event_code>/signmode')
def signmode(event_code):
    version = _getResultVersion(event_code)
    time = version.filetimestamp
    time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    event_classes = EventClass.query.filter_by(event=event_code, is_team_class=False).all()

    signresults = {}
    num_starts = 0
    for ec in event_classes:
        indv_results = Result.query.filter_by(version=version.id, class_code=ec.class_code).all()
        indv_results.sort(cmp=_sortResults)
        num_starts += len(indv_results)
        signresults[ec.class_code] = indv_results

    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name

    return render_template('signmode.html', config=RenderConfig,
                                            time=time,
                                            event=event,
                                            classes=event_classes,
                                            starts=num_starts,
                                            results=signresults, 
                                            clubs=clubs)

@frontend.route('/event/<event_code>/results/<indv_class>')
def event_class_result_indv(event_code, indv_class):
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    class_info = EventClass.query.filter_by(event=event_code, class_code=indv_class).first_or_404()

    version = _getResultVersion(event_code)
    v = version.id
    indv_results = Result.query.filter_by(version=v, class_code=indv_class).all()
    indv_results.sort(cmp=_sortResults)
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    time = version.filetimestamp

    return render_template('EventResultTable.html', config=RenderConfig, 
                                                    time=time, 
                                                    event=event,
                                                    class_info=class_info,
                                                    clubs=club_lookup,
                                                    results=indv_results)

def _sortResults(A, B):
    if A.position>0 and B.position>0:
        return A.position - B.position
    elif (A.position>0) and (B.position<0):
        return -1
    elif (B.position>0) and (A.position<0):
        return 1
    else:
        if A.score and B.score:
            return int(A.score - B.score)
        else:
            return 0

@frontend.route('/results/teams')
def team_class_select():
    time = datetime.now()
    return render_template('TeamResultClassSelection.html', time=time)
    
@frontend.route('/event/<event_code>/results/teams/<team_class>')
def event_class_result_team(event_code, team_class):
    version = _getResultVersion(event_code)
    v = version.id
    teamdata = TeamResult.query.filter_by(version=v, class_code=team_class).order_by(TeamResult.position).all()
    teamnames = {}
    c = Club.query.all()
    for club in c:
        teamnames[club.club_code] = club.club_name
    classinfo = EventClass.query.filter_by(event=event_code, class_code=team_class).one()
    teamscorers = Result.query.filter_by(version=v).filter((Result.class_code.startswith(team_class[:-1]))).filter_by(is_team_scorer=True).order_by(Result.club_code, -Result.score).all()

    time = version.filetimestamp
    return render_template('TeamResultTable.html', config=RenderConfig,
                                                   time=time,
                                                   cclass=classinfo,
                                                   teams=teamdata,
                                                   clubs=teamnames,
                                                   members=teamscorers)


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
    time = datetime.now()
    return render_template('meetstats.html', config=RenderConfig, time=time, checked=checked, downloaded=len(download_sicards), out=checked-fin, items=out_items)
    

def _getResultVersion(event):
    v = Version.query.filter_by(event=event, ready=True).order_by('-id').first()
    if v == None:
        return Version(event, None)
    return v