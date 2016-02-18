from flask import Blueprint, request, abort, render_template

from .models import db, Result, RemotePunch, Club, Cclass, TeamResult

import copy

frontend = Blueprint("frontend", __name__)

@frontend.route('/')
def home():
    return render_template('COCwifihome.html')
    
@frontend.route('/results/teams')
def team_class_select():
    return render_template('TeamResultClassSelection.html')
    
@frontend.route('/results/teams/<cclass>')
def cclass_team_results(cclass):
    teamdata = TeamResult.query.filter_by(cclassshort=cclass).order_by(TeamResult.position)
    teamnames = {}
    c = Club.query.all()
    for club in c:
        teamnames[club.clubshort] = club.clubfull
    classinfo = Cclass.query.filter_by(cclassshort=cclass).one()
    teamscorers = Result.query.filter((Result.cclassshort.startswith(cclass))).filter_by(isTeamScorer=True).order_by(Result.clubshort, -Result.score).all()
    
    return render_template('TeamResultTable.html', cclass=classinfo, teams=teamdata, clubs=teamnames, members=teamscorers)

@frontend.route('/results/<cclass>')
def cclass_results(cclass):
    knownclass = Cclass.query.all()
    if cclass not in [c.cclassshort for c in knownclass]:
        return '404: Not found. Unknown competition class: {}'.format(cclass), 404
    q = Result.query.filter_by(cclassshort=cclass).all()
    c = Club.query.all()
    cd = {}
    for club in c:
        cd[club.clubshort] = club.clubfull
    classinfo = Cclass.query.filter_by(cclassshort=cclass).one()
    return render_template('resulttable.html', cclass=classinfo, items=q, clubs=cd)


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

    return render_template('AwardsTable.html', indvawards=individualclasses, teamawards=teamclasses, clubs=cd)

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