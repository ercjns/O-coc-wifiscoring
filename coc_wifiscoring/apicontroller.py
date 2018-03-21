from flask import Blueprint, request, abort, render_template
from datetime import datetime
from os import remove
import time

from .models import *

import ETL as ETL


API = Blueprint("resultsAPI", __name__)

@API.route('/event/<event>/results', methods=['GET', 'POST'])
def results(event):
    if request.method == 'GET':
        # try:
        q = Result.query.filter_by(event=event).all()
        return render_template('basiclist.html', items=q)
        # except:
        #     abort(404)

    elif request.method == 'POST':
        timeStart_postResults = time.time()
        try:
            request.files[request.files.keys()[0]].save('latestResultsXML.xml')
        except:
            return 'Please upload an IOF XML ResultsList', 400

        try:
            timeStart_getRunners = time.time()
            results, timestamp = ETL.getRunners('latestResultsXML.xml')
            timeEnd_getRunners = time.time()
        except:
            remove('latestResultsXML.xml')
            return 'GetRunners failed. :(', 500

        newVersion = Version(event, timestamp)
        db.session.add(newVersion)
        db.session.commit()
        version = Version.query.filter_by(event=event).order_by(Version.id.desc()).first()
        v = version.id

        try:
            timeStart_buildDB = time.time()
            for r in results:
                result_dict = { 'sicard': int(r['estick'] if r['estick']>0 else -1),
                                'name': str(r['name']),
                                'bib': int(r['bib'] if r['bib']>0 else -1),
                                'class_code': str(r['class_code']),
                                'club_code': str(r['club']),
                                'time': int(r['time'] if r['time']>0 else -1),
                                'status': str(r['status'])
                              }
                new_result = Result(event, v, result_dict)
                db.session.add(new_result)
            db.session.commit()
            timeEnd_buildDB = time.time()
        except:
            remove('latestResultsXML.xml')
            return 'Problem building up the db refresh', 500

        try:
            timeStart_assignPos = time.time()
            _assignPositions(event, v)
            timeEnd_assignPos = time.time()
            timeStart_assignScore = time.time()
            _assignScores(event, v)
            timeEnd_assignScore = time.time()
        except:
            remove('latestResultsXML.xml')
            return 'Problem assigning individual positions and scores', 500

        try:
            timeStart_teamScore = time.time()
            _assignTeamScores(event, v)
            timeEnd_teamScore = time.time()
            timeStart_teamPos = time.time()
            _assignTeamPositions(event, v)
            timeEnd_teamPos = time.time()
        except:
            remove('latestResultsXML.xml')
            return 'Problem assigning team scores and positions', 500

        version.ready = True
        db.session.add(version)
        db.session.commit()

        # TODO: think about deleting old versions from the db
        remove('latestResultsXML.xml')

        timeEnd_postResults = time.time()

        # print('{:.4f}s for getRunners'.format(timeEnd_getRunners - timeStart_getRunners))
        # print('{:.4f}s for buildDB'.format(timeEnd_buildDB - timeStart_buildDB))
        # print('{:.4f}s for assignPos'.format(timeEnd_assignPos - timeStart_assignPos))
        # print('{:.4f}s for assignScore'.format(timeEnd_assignScore - timeStart_assignScore))
        # print('{:.4f}s for teamScore'.format(timeEnd_teamScore - timeStart_teamScore))
        # print('{:.4f}s for teamPos'.format(timeEnd_teamPos - timeStart_teamPos))
        # print('{:.4f}s to complete postResults'.format(timeEnd_postResults - timeStart_postResults))

        return 'New Results: {}'.format(version.id), 200

def _assignPositions(event, v):
    event_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=False).all()
    for c in event_classes:
        class_results = Result.query.filter_by(version=v).filter_by(class_code=c.class_code).filter_by(status="OK").order_by(Result.time).all()
        if len(class_results) == 0: 
            # print 'No results for {}'.format(c.class_name)
            continue
        nextposition = 1
        for i in range(len(class_results)):
            if i == 0:
                class_results[i].position = nextposition
            elif class_results[i].time == class_results[i-1].time:
                class_results[i].position = class_results[i-1].position
            else:
                class_results[i].position = nextposition
            nextposition += 1
        db.session.add_all(class_results)
    db.session.commit()
    return

def _assignScores(event, v):
    event_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=False).all()
    for c in event_classes:
        if not Result.query.filter_by(version=v).filter_by(class_code=c.class_code).all():
            continue
        if c.score_method == '':
            continue
            
        elif c.score_method == 'WIOL-indv':
            class_results = Result.query.filter_by(version=v).filter_by(class_code=c.class_code).all()
            for r in class_results:
                if r.position < 0:
                    r.score = 0
                elif r.position == 0:
                    raise ValueError
                elif r.position == 1: r.score = 100
                elif r.position == 2: r.score = 95
                elif r.position == 3: r.score = 92
                else:
                    r.score = 100 - 6 - int(r.position)
            db.session.add_all(class_results)

        elif c.score_method == 'NOCI-indv':
            class_results = Result.query.filter_by(version=v).filter_by(class_code=c.class_code).all()
            awt = sum([r.time for r in class_results if (r.position > 0 and r.position <=3)]) / 3.0

            if c.class_code == 'N2M':
                paired_class_code = 'N3F'
            elif c.class_code == 'N3F':
                paired_class_code = 'N2M'
            elif c.class_code == 'N4F':
                paired_class_code = 'N5M'
            elif c.class_code == 'N5M':
                paired_class_code = 'N4F'
            elif c.class_code == 'N1F':
                paired_class_code = 'N1M'
            elif c.class_code == 'N1M':
                paired_class_code = 'N1F'
            else:
                paired_class_code = 'none'

            try:
                paired_results = Result.query.filter_by(version=v).filter_by(class_code=paired_class_code).all()
                paired_awt = sum([r.time for r in paired_results if (r.position > 0 and r.position <=3)]) / 3.0
                better_awt = awt if awt < paired_awt else paired_awt
            except:
                better_awt = 60 * 3 * 3600

            for r in class_results:
                if r.status in ['OK']:
                    r.score = 60 * r.time / awt
                else:
                    r.score = (60 * (3*3600) / better_awt) + 10
            db.session.add_all(class_results)

        elif c.score_method == 'ULT-indv':
            class_results = Result.query.filter_by(version=v).filter_by(class_code=c.class_code).filter(Result.position > 0).all()
            try:
                winner = Result.query.filter_by(version=v).filter_by(class_code=c.class_code).filter_by(position=1).one()
                benchmark = float(winner.time)
            except:
                # no winner found, assign no scores.
                continue
            for r in class_results:
                if r.time:
                    r.score = round( (benchmark / r.time) * 1000 )
                else:
                    r.score = 0
            db.session.add_all(class_results)

    db.session.commit()
    return

def _assignTeamScores(event, v):
    event_team_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=True).all()
    for c in event_team_classes:
        if c.score_method == '':
            continue

        elif c.score_method == 'WIOL-team':
            indv_results = []
            for indv_class in c.team_classes.split('-'):
                indv_class = indv_class.strip()
                indv_results += Result.query.filter_by(version=v).filter_by(class_code=indv_class).all()
            teams = set([r.club_code for r in indv_results])
            for team in teams:
                score = 0
                contributors = 0
                members = [r for r in indv_results if ((r.club_code == team) and (r.score > 0))]
                members.sort(key=lambda x: -x.score)
                while ((len(members) > 0) and (contributors < 3)):
                    scorer = members.pop(0)
                    score += scorer.score
                    scorer.is_team_scorer = True
                    contributors += 1
                    db.session.add(scorer)
                if members:
                    for nonscorer in members:
                        nonscorer.is_team_scorer = False
                    db.session.add_all(members)
                team = TeamResult(event, v, c.class_code, team, score, True)
                db.session.add(team)

        elif c.score_method == 'NOCI-team':
            indv_results = []
            for indv_class in c.team_classes.split('-'):
                indv_class = indv_class.strip()
                indv_results += Result.query.filter_by(version=v).filter_by(class_code=indv_class).all()
            teams = set([r.club_code for r in indv_results])
            for team in teams:
                score = 0
                contributors = 0
                members = [r for r in indv_results if (r.club_code == team)]
                members.sort(key=lambda x: x.score)
                while ((len(members) > 0) and (contributors < 3)):
                    scorer = members.pop(0)
                    score += scorer.score
                    scorer.is_team_scorer = True
                    contributors += 1
                    db.session.add(scorer)
                if members:
                    for nonscorer in members:
                        nonscorer.isTeamScorer = False
                    db.session.add_all(members)
                valid = True if contributors == 3 else False
                team = TeamResult(event, v, c.class_code, team, score, valid)
                db.session.add(team)

    db.session.commit()
    return

def _assignTeamPositions(event, v):
    event_team_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=True).all()
    for c in event_team_classes:
        if c.score_method == '':
            continue

        elif c.score_method == 'WIOL-team':
            team_results = TeamResult.query.filter_by(version=v).filter_by(class_code=c.class_code).all()
            team_results.sort(key=lambda x: -x.score)
            nextposition = 1
            for i in range(len(team_results)):
                if i == 0:
                    team_results[i].position = nextposition
                elif team_results[i].score < team_results[i-1].score:
                    team_results[i].position = nextposition
                else:
                    a_club = team_results[i-1].club_code
                    b_club = team_results[i].club_code
                    a_scorers = []
                    b_scorers = []
                    for indv_class in c.team_classes.split('-'):
                        indv_class = indv_class.strip()
                        a_scorers += Result.query.filter_by(event=event, version=v, class_code=indv_class, club_code=a_club, is_team_scorer=True).all()
                        b_scorers += Result.query.filter_by(event=event, version=v, class_code=indv_class, club_code=b_club, is_team_scorer=True).all()
                    a_scorers.sort(key=lambda x: -x.score)
                    b_scorers.sort(key=lambda x: -x.score)
                    while a_scorers and b_scorers:
                        tiebreakerA = a_scorers.pop(0).score
                        tiebreakerB = b_scorers.pop(0).score
                        if tiebreakerA > tiebreakerB:
                            # print('A wins, assign next position to B\n')
                            team_results[i].position = nextposition
                            break
                        elif tiebreakerB > tiebreakerA:
                            # print('B wins, swapping positions\n')
                            team_results[i].position = team_results[i-1].position
                            team_results[i-1].position = nextposition
                            break
                        else:
                            continue
                    if team_results[i].position == None:
                        if a_scorers:
                            # print('A wins, assign next position to B\n')
                            team_results[i].posoition = nextposition
                            break
                        elif b_scorers:
                            # print('B wins, swapping positions\n')
                            team_results[i].position = team_results[i-1].position
                            team_results[i-1].position = nextposition
                            break
                        else:
                            # print('Actually a Tie!\n')
                            team_results[i].position = team_results[i-1].position
                nextposition += 1
            db.session.add_all(team_results)

        elif c.score_method == 'NOCI-team':
            team_results = TeamResult.query.filter_by(version=v, class_code=c.class_code, is_valid=True).all()
            team_results.sort(key=lambda x: x.score)
            nextposition = 1
            for i in range(len(team_results)):
                if i == 0:
                    team_results[i].position = nextposition
                elif team_results[i].score == team_results[i-1].score:
                    team_results[i].position = team_results[i-1].position
                else:
                    team_results[i].position = nextposition
                nextposition += 1
            db.session.add_all(team_results)

    db.session.commit()
    return

@API.route('/teams', methods=['GET'])
def teams():
    q = TeamResult.query.all()
    return render_template('basiclist.html', items = q)
        

@API.route('/clubs', methods=['GET', 'PUT', 'DELETE'])
def clubs():
    """ Mapping of Club/Team code to full name
    
    GET returns a view of all clubs
    PUT accepts a list of clubs and will update data
    DELETE will clear the entire collection
    """
    
    if request.method == 'GET':
        q = Club.query.all()
        return render_template('basiclist.html', items=q)

    elif request.method == 'PUT':
        f = request.files[request.files.keys()[0]]
        clubs = ETL.clubcodejson(f)
        for club in clubs:
            # abbr = club['abbr']
            abbr = club['code']
            full = club['name']
            q = Club.query.filter_by(club_code=abbr).all()
            
            if len(q) > 2:
                return 'Internal Error: Multiple clubs found for ' + abbr, 500
                
            if not q:
                new_club = Club(abbr, full)
                db.session.add(new_club)
                
            elif q:
                existing_club = q[0]
                if existing_club.club_name != full:
                    existing_club.club_name = full
                    db.session.add(existing_club)
                    
        db.session.commit()
        return 'Clubs table updated', 200

    elif request.method == 'DELETE':
        pass
        

@API.route('/event/<event>/classes', methods=['GET', 'PUT', 'DELETE'])
def cclasses(event):
    """ Mapping of class code to full name
    
    GET returns a view of all classes
    PUT accepts a list of classes and will update data
    DELETE will clear the entire collection
    """
    
    if request.method == 'GET':
        q = EventClass.query.filter_by(event=event).all()
        return render_template('basiclist.html', items=q)

    elif request.method == 'PUT':
        # TODO: make this a PUT rather than a wipe and reload.
        EventClass.query.filter_by(event=event).delete()

        f = request.files[request.files.keys()[0]].save('~latestclassinfo.csv')
        with open('~latestclassinfo.csv') as infile:
            # eventClasses = ETL.classCSV('~latestclassinfo.csv')
            eventClasses = ETL.classCSV(infile)
            for c in eventClasses:
                new_class = EventClass(event, c)
                db.session.add(new_class)
            db.session.commit()
        remove(f)
        return 'Refreshed EventClass table', 200

    elif request.method == 'DELETE':
        pass

@API.route('/events', methods=['GET', 'PUT', 'DELETE'])
def events():
    """ Mapping of class code to full name
    
    GET returns a view of all classes
    PUT accepts a list of classes and will update data
    DELETE will clear the entire collection
    """
    
    if request.method == 'GET':
        q = Event.query.all()
        return render_template('basiclist.html', items=q)

    elif request.method == 'PUT':
        f = request.files[request.files.keys()[0]].save('~latesteventinfo.tsv')
        events = ETL.eventsTSV('~latesteventinfo.tsv')

        # TODO: make this a PUT rather than a wipe and reload.
        Event.query.delete()

        for e in events:
            new_event = Event(e['event_code'], e['event_name'], e['date'], e['venue'], e['description'])
            db.session.add(new_event)
        db.session.commit()
        remove(f)
        return 'Refreshed Event table', 200

    elif request.method == 'DELETE':
        pass
        
@API.route('/event/<event>/entries', methods=['GET','PUT'])
def entries(event):
    """ Name to class and SIcard mapping
    
    GET returns evertyhing
    PUT accepts an iof3 XML entries list and updates data
    DELETE clears the collection
    """
    if request.method == 'GET':
        q = Entry.query.filter_by(event=event).all()
        return render_template('basiclist.html', items=q)
        
    if request.method == 'PUT':
        request.files[request.files.keys()[0]].save('entries.xml')
        entries = ETL.entriesXML3('entries.xml')
        for e in entries:
            new_entry = Entry(event, e['name'], e['cclass'], e['club'], e['sicard'])
            db.session.add(new_entry)
        db.session.commit()
        return 'Updated Entries', 200