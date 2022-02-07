from flask import Blueprint, request, abort, render_template, redirect, url_for
from werkzeug.routing import RequestRedirect
from .models import *
import copy
from datetime import datetime


frontend = Blueprint("frontend", __name__)

RenderConfig = {}
RenderConfig['BrandLarge'] = 'COC-logo-diamond-red-large.png'
# RenderConfig['BrandLarge'] = 'armadillo.png'

WIOL_CLASSES = ['W1F', 'W1M', 'W2F', 'W2M', 'W3F', 'W3M', 'W4F', 'W5M', 'W5FIC', 'W5MIC', 'W6F', 'W6M', 'W8F', 'W8M']
WIOL_TEAM_CLASSES = ['W2T', 'W3FT', 'W3MT', 'W4FT', 'W5MT', 'W6FT', 'W6MT', 'W8FT', 'W8MT']
IC_CLASSES = []
IC_TEAM_CLASSES = []

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
    event = _get_event_or_redirect(event_code)
    event_classes = EventClass.query.filter_by(event=event_code).all()

    wiol = [c for c in event_classes if c.class_code in WIOL_CLASSES]
    wiolT = [c for c in event_classes if c.class_code in WIOL_TEAM_CLASSES]
    icT = [c for c in event_classes if c.class_code in IC_TEAM_CLASSES]
    public = [c for c in event_classes if c not in wiol + wiolT + icT]

    wiol.sort(key=lambda x: x.class_code, cmp=compare_class_codes)
    wiolT.sort(key=lambda x: x.class_code, cmp=compare_class_codes)
    icT.sort(key=lambda x: x.class_code, cmp=compare_class_codes)
    public.sort(key=lambda x: x.class_code, cmp=compare_class_codes)

    return render_template('EventClassSelect.html', config=RenderConfig, 
                                                    time=time, 
                                                    event=event,
                                                    wiol=wiol, 
                                                    wiolT=wiolT,
                                                    icT=icT,
                                                    public=public)

@frontend.route('/event/<event_code>/bigscreen')
def bigscreen(event_code):
    exclude = request.args.get('x', '').upper().split(',')
    include = request.args.get('i', '').upper().split(',')
    dwell = request.args.get('dwell', 10)
    try:
        dwell = float(dwell)
    except:
        dwell = 10

    if not (exclude == [''] or include == ['']):
        # only use one of exclude or include
        exclude = []
        include = []
    else:
        if include == ['']: include = []
        if exclude == ['']: exclude = []

    version = _getResultVersion(event_code)
    time = version.filetimestamp
    if time == None:
        time = datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    else:
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

    event = _get_event_or_redirect(event_code)
    event_classes = EventClass.query.filter_by(event=event_code, is_team_class=False).all()

    if exclude:
        event_classes = [x for x in event_classes if x.class_code not in exclude]
    if include:
        event_classes = [x for x in event_classes if x.class_code in include]

    tvresults = {}
    num_starts = 0
    for ec in event_classes:
        indv_results = Result.query.filter_by(version=version.id, class_code=ec.class_code).all()
        indv_results.sort(cmp=_sortResults)
        num_starts += len(indv_results)
        tvresults[ec.class_code] = indv_results

    tvresults_teams = {}
    event_team_classes = []
    if 'TEAMS' not in exclude:
        event_team_classes = EventClass.query.filter_by(event=event_code, is_team_class=True).all()
        if exclude:
            event_team_classes = [x for x in event_team_classes if x.class_code not in exclude]
        if include:
            if 'TEAMS' not in include:
                event_team_classes = [x for x in event_team_classes if x.class_code in include]
        for etc in event_team_classes:
            if etc.class_code in exclude:
                event_team_classes.remove(etc)
                continue
            team_results = TeamResult.query.filter_by(version=version.id, class_code=etc.class_code).order_by(TeamResult.position).all()
            tvresults_teams[etc.class_code] = team_results

    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name

    return render_template('bigscreen.html',
                            config=RenderConfig,
                            time=time,
                            event=event,
                            classes=event_classes,
                            classes_teams=event_team_classes,
                            clubs=club_lookup,
                            results_indv=tvresults,
                            results_teams=tvresults_teams,
                            dwell=dwell

    )


@frontend.route('/event/<event_code>/signmode')
def signmode(event_code):
    exclude = request.args.get('x', '').upper().split(',')
    include = request.args.get('i', '').upper().split(',')

    if not (exclude == [''] or include == ['']):
        # only use one of exclude or include
        exclude = []
        include = []
    else:
        if include == ['']: include = []
        if exclude == ['']: exclude = []

    version = _getResultVersion(event_code)
    time = version.filetimestamp
    if time == None:
        time = datetime.strptime('2000-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    else:
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    event = _get_event_or_redirect(event_code)
    event_classes = EventClass.query.filter_by(event=event_code, is_team_class=False).all()

    if exclude:
        event_classes = [x for x in event_classes if x.class_code not in exclude]
    if include:
        event_classes = [x for x in event_classes if x.class_code in include]

    signresults = {}
    num_starts = 0
    for ec in event_classes:
        indv_results = Result.query.filter_by(version=version.id, class_code=ec.class_code).all()
        indv_results.sort(cmp=_sortResults)
        num_starts += len(indv_results)
        signresults[ec.class_code] = indv_results

    signresults_teams = {}
    event_team_classes = []
    if 'TEAMS' not in exclude:
        event_team_classes = EventClass.query.filter_by(event=event_code, is_team_class=True).all()
        if exclude:
            event_team_classes = [x for x in event_team_classes if x.class_code not in exclude]
        if include:
            if 'TEAMS' not in include:
                event_team_classes = [x for x in event_team_classes if x.class_code in include]
        for etc in event_team_classes:
            if etc.class_code in exclude:
                event_team_classes.remove(etc)
                continue
            team_results = TeamResult.query.filter_by(version=version.id, class_code=etc.class_code).order_by(TeamResult.position).all()
            signresults_teams[etc.class_code] = team_results

    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name

    return render_template('signmode.html', config=RenderConfig,
                                            time=time,
                                            event=event,
                                            starts=num_starts,
                                            classes=event_classes,
                                            results=signresults,
                                            classes_teams=event_team_classes,
                                            results_teams=signresults_teams,
                                            clubs=club_lookup)

@frontend.route('/event/<event_code>/results/<indv_class>')
def event_class_result_indv(event_code, indv_class):
    event = _get_event_or_redirect(event_code)
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
    event = _get_event_or_redirect(event_code)
    version = _getResultVersion(event_code)
    v = version.id
    classinfo = EventClass.query.filter_by(event=event_code, class_code=team_class).one()
    
    teamdata = TeamResult.query.filter_by(version=v, class_code=team_class).order_by(TeamResult.position).all()
    
    teamscorers = Result.query.filter_by(version=v).filter((Result.class_code.startswith(team_class[:-1]))).filter_by(is_team_scorer=True)
    if classinfo.score_method == 'WIOL-team':
        # higher score is better
        teamscorers = teamscorers.order_by(Result.club_code, -Result.score).all()
    else:
        # lower score is better
        teamscorers = teamscorers.order_by(Result.club_code, Result.score).all()

    for t in teamdata:
        t.membercount = len([m for m in teamscorers if m.club_code == t.club_code])
    teamdata.sort(cmp=_sortTeamResults)

    teamnames = {}
    c = Club.query.all()
    for club in c:
        teamnames[club.club_code] = club.club_name

    time = version.filetimestamp
    return render_template('TeamResultTable.html', config=RenderConfig,
                                                   time=time,
                                                   cclass=classinfo,
                                                   teams=teamdata,
                                                   clubs=teamnames,
                                                   members=teamscorers)

def _sortTeamResults(A, B):
    if A.position>0 and B.position>0:
        return A.position - B.position
    elif A.is_valid and not B.is_valid:
        return -1
    elif not A.is_valid and B.is_valid:
        return 1
    # sort "invalid" results logically
    else:
        # more members is better
        if A.membercount != B.membercount:
            return B.membercount - A.membercount 
        # lower score is better
        if A.score and B.score:
            return int(A.score - B.score)
        else:
            return 0

# @frontend.route('/meetstats/')
# def meet_stats():
#     download_items = Result.query.all()
#     download_sicards = [a.sicard for a in download_items]
    
#     check_items = RemotePunch.query.filter_by(station=17).group_by(RemotePunch.sicard).order_by(RemotePunch.time).all()
    
#     fin = len(download_sicards)
#     checked = 0
    
#     out_items = []
#     for card in check_items:
#         if card.sicard not in download_sicards:
#             checked += 1
#             out_items.append(card)
#             continue

#     checked += fin
#     time = datetime.now()
#     return render_template('meetstats.html', config=RenderConfig, time=time, checked=checked, downloaded=len(download_sicards), out=checked-fin, items=out_items)


def _getResultVersion(event):
    v = Version.query.filter_by(event=event, ready=True).order_by(Version.id.desc()).first()
    if v == None:
        return Version(event, None)
    return v

def _get_event_or_redirect(event_code):
    event = Event.query.filter_by(event_code=event_code).first()
    if event is not None:
        return event
    else:
        raise RequestRedirect(url_for('frontend.home'))

def compare_class_codes(a, b):
    # 1 if a > b, -1 if a < b.
    # True == later in alpha order
    # order groups later than individual categories
    if (a[-1] == 'G' or b[-1] == 'G') and a[:-1] == b[:-1]:
        if a[-1] == 'G' and b[-1] != 'G':
            return 1
        elif a[-1] != 'G' and b[-1] == 'G':
            return -1
        else:
            return 0
    # order intercollegiate after wiol varsity
    elif ((a[0] == '9' or b[0] == '9') and (a[0] == 'W' or b[0] == 'W')):
        if a[0] == '9':
            return 1
        elif b[0] == '9':
            return -1
    else:
        if a > b:
            return 1
        elif b > a:
            return -1
        elif a == b:
            return 0
        else:
            raise ValueError("can't compare {} and {}".format(a,b))
