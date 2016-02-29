from flask import Blueprint, request, abort, render_template
from .models import *
import copy

frontend = Blueprint("frontend", __name__)

@frontend.route('/')
def home():
    time = _getResultTimestamp()
    events = Event.query.all()
    
    return render_template('NOCIhome.html', time=time, events=events)

@frontend.route('/event/<event_code>/')
def event_class_select(event_code):
    time = _getResultTimestamp()
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    event_classes = EventClass.query.filter_by(event=event_code, is_team_class=False).all()
    noci_classes = [c for c in event_classes if (c.class_code[0] == 'N' and c.class_code[2] != 'I')]
    noci_classes.sort(key=lambda x: x.class_code)
    try:
        noci_classes.append(next(c for c in event_classes if c.class_code == 'N4I'))
    except:
        pass
    ult_classes = [c for c in event_classes if c.class_code[0] != 'N']
    ult_classes.sort(key=lambda x: x.class_code)
    
    return render_template('EventClassSelect.html', time=time, 
                                                    event=event,
                                                    noci_classes=noci_classes, 
                                                    ult_classes=ult_classes)

@frontend.route('/noci/individual')
def noci_results_indv():
    time = _getResultTimestamp()
    event_classes = EventClass.query.filter_by(event=event, is_team_class=False, multi_score_method='time-total').all()
    
    return render_template('EventClassSelect.html', time=time, classes=event_classes)
    
@frontend.route('/noci/team')
def noci_results_team():
    time = _getResultTimestamp()
    event_classes = EventClass.query.filter_by(event=event, is_team_class=True, multi_score_method='NOCI-multi').all()
    
    return render_template('EventClassSelect.html', time=time, classes=event_classes)
    
@frontend.route('/results/teams')
def team_class_select():
    time = _getResultTimestamp()
    return render_template('TeamResultClassSelection.html', time=time)
    
@frontend.route('/results/teams/<cclass>')
def cclass_team_results(cclass):
    teamdata = TeamResult.query.filter_by(cclassshort=cclass).order_by(TeamResult.position)
    teamnames = {}
    c = Club.query.all()
    for club in c:
        teamnames[club.clubshort] = club.clubfull
    classinfo = Cclass.query.filter_by(cclassshort=cclass).one()
    teamscorers = Result.query.filter((Result.cclassshort.startswith(cclass))).filter_by(isTeamScorer=True).order_by(Result.clubshort, -Result.score).all()
    
    time = _getResultTimestamp()
    return render_template('TeamResultTable.html', time=time, cclass=classinfo, teams=teamdata, clubs=teamnames, members=teamscorers)

@frontend.route('/event/<event_code>/results/<indv_class>')
def event_class_result_indv(event_code, indv_class):
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    class_info = EventClass.query.filter_by(event=event_code, class_code=indv_class).first_or_404()
    indv_results = Result.query.filter_by(event=event_code, class_code=indv_class).all()
    indv_results.sort(cmp=_sortResults)
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    time = _getResultTimestamp()

    return render_template('EventResultTable.html', time=time, 
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
            return A.score - B.score
        else:
            return 0
        

@frontend.route('/results/')
def all_results():
    q = Result.query.all()
    return render_template('allresults.html', items=q)
    
@frontend.route('/awards/')
def awards():
    individualwinners = Result.query.filter(Result.position>0, Result.position<4).order_by(Result.position).all()
    scoredclasses = Cclass.query.filter_by(isScored=True).all()
    individualclasses = copy.deepcopy(scoredclasses)
    
    empties = []
    for ic in individualclasses:
        ic.winners = [i for i in individualwinners if i.cclassshort == ic.cclassshort]
        if ic.winners == []:
            empties.append(ic)
    for ic in empties:
        individualclasses.pop(individualclasses.index(ic))
    individualclasses.sort(key=lambda x: x.cclassshort)
    
    teamwinners = TeamResult.query.filter(TeamResult.position>0, TeamResult.position<4).order_by(TeamResult.position).all()
    teamclasses = copy.deepcopy(scoredclasses)

    empties = []
    for tc in teamclasses:
        tc.winners = [t for t in teamwinners if t.cclassshort == tc.cclassshort]
        if tc.winners == []:
            empties.append(tc)
    for tc in empties:
        teamclasses.pop(teamclasses.index(tc))
    teamclasses.sort(key=lambda x: x.cclassshort)

    c = Club.query.all()
    cd = {}
    for club in c:
        cd[club.clubshort] = club.clubfull

    time = _getResultTimestamp()
    return render_template('AwardsTable.html', time=time, indvawards=individualclasses, teamawards=teamclasses, clubs=cd)

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
    time = _getResultTimestamp()
    return render_template('meetstats.html', time=time, checked=checked, downloaded=len(download_sicards), out=checked-fin, items=out_items)
    

def _getResultTimestamp():
    time = DBAction.query.order_by(-DBAction.id).first()
    if time:
        return time.time.strftime('%H:%M, %b %d, %Y')
    else:
        return None

