from flask import Blueprint, request, abort, render_template, redirect, url_for
from .models import *
import copy

frontend = Blueprint("frontend", __name__)

@frontend.route('/')
def home():
    # time = _getResultTimestamp()
    # events = Event.query.all()
    # event_code = events[0].event_code # events and classes are pre-populated, this is almost a hard-code
    # noci_team_classes = EventClass.query.filter_by(event=event_code, is_team_class=True, multi_score_method='NOCI-multi').all()
    # noci_indv_classes = EventClass.query.filter_by(event=event_code, is_team_class=False, multi_score_method='time-total').all()
    
    # return render_template('NOCIhome.html', time=time, events=events, noci_team_classes=noci_team_classes, noci_indv_classes=noci_indv_classes)

    return render_template('COCwifihome.html', event='2016-01-09-1') #hard-code event code

@frontend.route('/event/<event_code>/')
def event_class_select(event_code):
    time = _getResultTimestamp()
    event = Event.query.filter_by(event_code=event_code).first_or_404()
    event_classes = EventClass.query.filter_by(event=event_code, is_team_class=False).all()
    wiol_classes = [c for c in event_classes if (c.class_code[0] == 'W')]
    public_classes = [c for c in event_classes if c not in wiol_classes]
    wiol_classes.sort(key=lambda x: x.class_code)
    public_classes.sort(key=lambda x: x.class_code)

    # noci_classes = [c for c in event_classes if (c.class_code[0] == 'N' and c.class_code[2] != 'I')]
    # noci_classes.sort(key=lambda x: x.class_code)
    # try:
    #     noci_classes.append(next(c for c in event_classes if c.class_code == 'N4I'))
    # except:
    #     pass
    # ult_classes = [c for c in event_classes if c.class_code[0] != 'N']
    # ult_classes.sort(key=lambda x: x.class_code)

    return render_template('EventClassSelect.html', time=time, 
                                                    event=event,
                                                    noci_classes=wiol_classes, 
                                                    ult_classes=public_classes)

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
            return int(A.score - B.score)
        else:
            return 0

            
@frontend.route('/ultseason/<class_code>')
def ult_season_standings(class_code):
    time = _getResultTimestamp()
    events = Event.query.all()
    class_info = EventClass.query.filter_by(event=events[0].event_code, class_code=class_code).first_or_404()
    #club lookup dict
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    
    multi_results = MultiResultIndv.query.filter_by(class_code=class_code).all()
    for m in multi_results:
        m.race_results = {}
        for r in m.result_ids.split('-'):
            r = r.strip()
            the_result = Result.query.get(r)
            m.race_results[the_result.event] = the_result
        m.name = the_result.name
        m.club_code = the_result.club_code
    multi_results.sort(cmp=_sortResults)
    
    return render_template('UltimateSeasonResults.html', time=time, 
                                                         results=multi_results, 
                                                         events=events,
                                                         class_info=class_info)
    
        
    
    
@frontend.route('/noci/individual/<class_code>')
def noci_results_indv(class_code):
    time = _getResultTimestamp()
    event_code = Event.query.first().event_code # events and classes are pre-populated, take whatever.
    class_info = EventClass.query.filter_by(event=event_code, class_code=class_code).first_or_404()
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    multi_results = MultiResultIndv.query.filter_by(class_code=class_code).all()
    for m in multi_results:
        m.results = []
        for r in m.result_ids.split('-'):
            r = r.strip()
            m.results.append(Result.query.get(r))
    multi_results.sort(cmp=_sortResults)
    
    return render_template('NOCItwoDayIndividualResults.html', time=time, 
                                                               class_info=class_info,
                                                               clubs=club_lookup,
                                                               results=multi_results)

                                                               
@frontend.route('/noci/team/<class_code>')
def noci_results_team(class_code):
    if class_code == 'NTU':
        return redirect(url_for('frontend.noci_results_champs'))
    time = _getResultTimestamp()
    event_code = Event.query.first().event_code # events and classes are pre-populated, take whatever.    
    class_info = EventClass.query.filter_by(event=event_code, class_code=class_code).first_or_404()
    indv_class_codes = [c.strip() for c in class_info.team_classes.split('-')]
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    multi_results = MultiResultTeam.query.filter_by(class_code=class_code).all()
    event_codes = []
    for m in multi_results:
        m.team_results = []
        for t in m.result_ids.split('-'):
            t = t.strip()
            team_result = TeamResult.query.get(t)
            m.team_results.append(team_result)
            if team_result.event not in event_codes:
                event_codes.append(team_result.event)
        m.team_results.sort(key=lambda x: x.event)
    
        m.members = {}
        indv_results = []
        for t in m.team_results:
            for c in indv_class_codes:
                indv_results += Result.query.filter_by(event=t.event, club_code=t.club_code, class_code=c).all()
            
            for r in indv_results:
                if r.bib not in m.members.keys():
                    m.members[r.bib] = {'name': r.name, 'club_code': r.club_code}
                m.members[r.bib][r.event] = r
    
    event_codes.sort()    
    multi_results.sort(cmp=_sortResults)
    
    
    return render_template('NOCItwoDayTeamResults.html', time=time, 
                                                         class_info=class_info,
                                                         clubs=club_lookup,
                                                         events=event_codes,
                                                         results=multi_results)
@frontend.route('/noci/teamchamps')
def noci_results_champs():
    time = _getResultTimestamp()
    class_info = EventClass.query.filter_by(class_code='NTU').first_or_404()
    clubs = Club.query.all()
    club_lookup = {}
    for club in clubs:
        club_lookup[club.club_code] = club.club_name
    champs_teams = MultiResultTeam.query.filter_by(class_code='NTU').all()
    for t in champs_teams:
        for cat in t.result_ids.split('-'):
            multi_result = MultiResultTeam.query.get(cat)
            if multi_result.class_code == 'NTV':
                t.v = multi_result
            elif multi_result.class_code == 'NTJV':
                t.jv = multi_result
    champs_teams.sort(cmp=_sortResults)
    
    return render_template('NOCItwoDayTeamChampResults.html', time=time,
                                                              class_info=class_info,
                                                              clubs=club_lookup,
                                                              results=champs_teams)
# @frontend.route('/results/teams')
# def team_class_select():
    # time = _getResultTimestamp()
    # return render_template('TeamResultClassSelection.html', time=time)
    
# @frontend.route('/results/teams/<cclass>')
# def cclass_team_results(cclass):
    # teamdata = TeamResult.query.filter_by(cclassshort=cclass).order_by(TeamResult.position)
    # teamnames = {}
    # c = Club.query.all()
    # for club in c:
        # teamnames[club.clubshort] = club.clubfull
    # classinfo = Cclass.query.filter_by(cclassshort=cclass).one()
    # teamscorers = Result.query.filter((Result.cclassshort.startswith(cclass))).filter_by(isTeamScorer=True).order_by(Result.clubshort, -Result.score).all()
    
    # time = _getResultTimestamp()
    # return render_template('TeamResultTable.html', time=time, cclass=classinfo, teams=teamdata, clubs=teamnames, members=teamscorers)


        

# @frontend.route('/results/')
# def all_results():
    # q = Result.query.all()
    # return render_template('allresults.html', items=q)
    
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
    action = DBAction.query.order_by(-DBAction.id).first()
    return str(action.time) if action else None
    # if time:
        # return time.time.strftime('%H:%M, %b %d, %Y')
    # else:
        # return None

