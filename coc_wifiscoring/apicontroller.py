from flask import Blueprint, request, abort, render_template
from datetime import datetime

from .models import *

import ETL as ETL


API = Blueprint("resultsAPI", __name__)

@API.route('/event/<event>/results', methods=['GET', 'POST'])
def results(event):
    if request.method == 'GET':
        #try:
        q = Result.query.filter_by(event=event).all()
        return render_template('basiclist.html', items=q)
        #except:
        #abort(404)

    elif request.method == 'POST':
        try:
            request.files[request.files.keys()[0]].save('latestResultsXML.xml')
        except:
            return 'Please upload an IOF XML ResultsList', 400

        try:
            results = ETL.getRunners('latestResultsXML.xml')
        except:
            return 'GetRunners failed. :(', 500

        #TODO: implement a primary/secondary db swap scheme, or only get deltas above.
        try:
            Result.query.filter_by(event=event).delete()
            TeamResult.query.filter_by(event=event).delete()
        except:
            return 'couldn\'t delete things', 500
        
        # try:
        for r in results:
            result_dict = { 'sicard': int(r['estick'] if r['estick']>0 else -1),
                            'name': str(r['name']),
                            'class_code': str(r['class_code']),
                            'club_code': str(r['club']),
                            'time': int(r['time'] if r['time']>0 else -1),
                            'status': str(r['status'])
                          }
            new_result = Result(event, result_dict)
            db.session.add(new_result)
            db.session.commit()
        # except:
            # return 'Problem building up the db refresh', 500
        
        # TODO these reference old names. Use "class_code" and "club_code" and "class_name" and "club_name"
        # try:
        _assignPositions(event)
        _assignScores(event)
            
        # except:
            # return 'Problem assigning positions or scores', 500
        
        _assignTeamScores(event)
        _assignTeamPositions(event)
        
        _assignMultiScores()

        new_action = DBAction(datetime.now(), 'results')
        db.session.add(new_action)
        db.session.commit()
        return 'Refreshed', 200

def _assignPositions(event):
    event_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=False).all()
    for c in event_classes:
        class_results = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).filter_by(status="OK").order_by(Result.time).all()
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

def _assignScores(event):
    event_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=False).all()
    for c in event_classes:
        if not Result.query.filter_by(event=event).filter_by(class_code=c.class_code).all():
            continue
        if c.score_method == '':
            continue
            
        elif c.score_method == 'WIOL-indv':
            class_finishers = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).filter(Result.position > 0).all()
            for r in class_finishers:
                if r.position == 1: r.score = 100
                elif r.position == 2: r.score == 95
                elif r.position ==3: r.score == 92
                else:
                    r.score = 100 - 6 - int(r.position)
            class_non_finishers = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).filter(Result.position < 0).all()
            if len(class_non_finishers) > 0:
                for r in class_non_finishers:
                    r.score = 0
            db.session.add_all(class_finishers)
            db.session.add_all(class_non_finishers)
            db.session.commit()
                
        elif c.score_method == 'NOCI-indv':
            class_results = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).all()
            awt = sum([r.time for r in classresults if (r.position > 0 and r.position <=3)]) / 3.0
            
            if c.class_code == 'N2M':
                paired_class_code = 'N3F'
            elif c.class_code == 'N3F':
                paired_class_code = 'N2M'
            elif c.class_code == 'N4F':
                paired_class_code = 'N5M'
            elif c.class_code == 'N5M':
                paired_class_code = 'N4F'    
            paired_results = Result.query.filter_by(event=event).filter_by(class_code=paired_class_code).all()
            paired_awt = sum([r.time for r in paired_results if (r.position > 0 and r.position <=3)]) / 3.0
            better_awt = awt if awt < paired_awt else paired_awt
            
            for r in class_results:
                if r.status in ['OK']:
                    r.score = 60 * r.time / awt
                else:
                    r.score = (60 * (3*3600) / better_awt) + 10
            db.session.add_all(class_results)
            db.session.commit()
        
        elif c.score_method == 'ULT-indv':
            class_results = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).filter(Result.position > 0).all()
            winner = Result.query.filter_by(event=event).filter_by(class_code=c.class_code).filter_by(position=1).all()
            print type(winner), winner
            benchmark = float(winner.time)
            for r in class_results:
                r.score = int( (benchmark / r.time) * 1000 )
            db.session.add_all(class_results)
            db.session.commit()

    return

def _assignTeamScores(event):
    event_team_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=True).all()
    for c in event_team_classes:
        if c.score_method == '':
            continue
            
        elif c.score_method == 'WIOL-team':
            indv_results = []
            for indv_class in c.team_classes.split('-'):
                indv_results += Result.query.filter_by(event=event).filter_by(class_code=indv_class).all()
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
                        nonscorer.isTeamScorer = False
                    db.session.add_all(members)
                team = TeamResult(event, c.class_code, team, score)
                db.session.add(team)
                db.session.commit()
    
        elif c.score_method == 'NOCI-team':
            indv_results = []
            for indv_class in c.team_classes.split('-'):
                indv_results += Result.query.filter_by(event=event).filter_by(class_code=indv_class).all()
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
                team = TeamResult(c.class_code, team, score)
                db.session.add(team)
                db.session.commit()

    return

def _assignTeamPositions(event):
    event_team_classes = EventClass.query.filter_by(event=event).filter_by(is_team_class=True).all()
    for c in event_team_classes:
        if c.score_method == '':
            continue
        
        elif c.score_method == 'WIOL-team':
            team_results = TeamResult.query.filter_by(event=event).filter_by(class_code=c.class_code).all()
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
                        a_scorers += Result.query.filter_by(event=event).filter_by(class_code=indv_class).filter_by(club_code=a_club).filter_by(is_team_scorer=True).all()
                        b_scorers +=Result.query.filter_by(event=event).filter_by(class_code=indv_class).filter_by(club_code=b_club).filter_by(is_team_scorer=True).all()
                    a_scorers.sort(key=lambda x: -x.score)
                    b_scorers.sort(key=lambda x: -x.score)
                    while a_scorers and b_scorers:
                        tiebreakerA = a_scorers.pop(0)
                        tiebreakerB = b_scorers.pop(0)
                        if tiebreakerA > tiebreakerB:
                            team_results[i].position = nextposition
                            break
                        elif tiebreakerB > tiebreakerA:
                            team_results[i].position = team_results[i-1].position
                            team_results[i-1].position = nextposition
                            break
                        else:
                            continue
                    if team_results[i].position == None:
                        if a_scorers:
                            team_results[i].posoition = nextposition
                        elif b_scorers:
                            team_results[i].position = team_results[i-1].position
                            team_results[i-1].position = nextposition
                            break
                        else:
                            team_results[i].position = team_results[i-1].position
                    nextposition += 1
            db.session.add_all(team_results)
            db.session.commit()
        
        elif c.score_method == 'NOCI-team':
            team_results = TeamResult.query.filter_by(event=event).filter_by(class_code=c.class_code).all()
            team_results.sort(key=lambda x: x.score)
            nextposition = 1
            for i in range(len(team_results)):
                if i == 0:
                    team_results[i].position = nextposition
                elif team_results[i].score == team_results[i-1].score:
                    team_results[i].position == team_results[i-1].position
                else:
                    team_results[i].position = nextposition
                nextposition += 1
            db.session.add_all(team_results)
            db.session.commit()
    return
    
def _assignMultiScores():
    multi_classes = EventClass.query.filter_by(is_team_class=False).fitler_by(is_multi_scored=True).all()
    for c in multi_classes:
        # ToDo: follow class's multi-score-method. Currently sums all scores.
        indv_results = Result.query.filter_by(class_code=c.class_code).order_by(Result.bib).all()
        bib = None
        score = 0
        ids = ''
        for r in indv_results:
            if r.bib != bib:
                if ids:
                   new_multi_result = MultiResultIndv(score, ids)
                   db.session.add(new_multi_result)
                bib = r.bib
                score = r.score
                ids = str(r.id)
            else:
                score += r.score
                ids += '-' + str(r.id)
        db.session.commit()
        
        
def _assignMultiPositions():
    multi_classes = EventClass.query.filter_by(is_team_class=False).fitler_by(is_multi_scored=True).all()
    for c in multi_classes:
        if c.multi_score_method == 'time-total':
            multi_results = MultiResultIndv.query.filter_by(class_code=c.class_code).all()
            multi_results.sort(key=lambda x: x.score) # Low is better
            nextposition = 1
            for i in range(len(multi_results)):
                if i == 0:
                    multi_results[i].position = nextposition
                elif multi_results[i].score == multi_results[i-1].score:
                    multi_results[i].position == multi_results[i-1].position
                else:
                    multi_results[i].position = nextposition
                nextposition += 1
            db.session.add_all(multi_results)
            db.session.commit()
            
        if c.multi_score_method == 'WIOL-season':
            multi_results = MultiResultIndv.query.filter_by(class_code=c.class_code).all()
            multi_results.sort(key=lambda x: -x.score) # High is better, sort high to the front with -x.
            nextposition = 1
            for i in range(len(multi_results)):
                if i == 0:
                    multi_results[i].position = nextposition
                elif multi_results[i].score == multi_results[i-1].score:
                    multi_results[i].position == multi_results[i-1].position
                else:
                    multi_results[i].position = nextposition
                nextposition += 1
                # TODO: Implement WIOL season tie-breaking
            db.session.add_all(multi_results)
            db.session.commit()
        
    

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
            abbr = club['abbr']
            full = club['name']
            q = Club.query.filter_by(club_code=abbr).all()
            
            if len(q) > 2:
                return 'Internal Error: Multiple clubs found for ' + abbr, 500
                
            if not q:
                new_club = Club(abbr, full)
                db.session.add(new_club)
                
            elif q:
                existing_club = q[0]
                if existing_club.clubfull != full:
                    existing_club.clubfull = full
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
        f = request.files[request.files.keys()[0]].save('~latestclassinfo.csv')
        eventClasses = ETL.classCSV('~latestclassinfo.csv')

        # TODO: make this a PUT rather than a wipe and reload.
        EventClass.query.filter_by(event=event).delete()

        for c in eventClasses:
            new_class = EventClass(event, c)
            db.session.add(new_class)
        db.session.commit()
        return 'Refreshed EventClass table', 200

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