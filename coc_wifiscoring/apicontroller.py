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
            results, timestamp = ETL.getRunners('latestResultsXML.xml')
        except:
            return 'GetRunners failed. :(', 500

        #TODO: implement a primary/secondary db swap scheme, or only get deltas above.
        try:
            Result.query.filter_by(event=event).delete()
            TeamResult.query.filter_by(event=event).delete()
        except:
            return 'couldn\'t delete things', 500
        
        try:
            for r in results:
                result_dict = { 'sicard': int(r['estick'] if r['estick']>0 else -1),
                                'name': str(r['name']),
                                'bib': int(r['bib'] if r['bib']>0 else -1),
                                'class_code': str(r['class_code']),
                                'club_code': str(r['club']),
                                'time': int(r['time'] if r['time']>0 else -1),
                                'status': str(r['status'])
                              }
                new_result = Result(event, result_dict)
                db.session.add(new_result)
                db.session.commit()
        except:
            return 'Problem building up the db refresh', 500
        
        # TODO these reference old names. Use "class_code" and "club_code" and "class_name" and "club_name"
        # try:
        _assignPositions(event)
        _assignScores(event)
        
        _assignTeamScores(event)
        _assignTeamPositions(event)
        
        _assignMultiScores(event)
        _assignMultiPositions(event)
            
        # except:
            # return 'Problem assigning positions or scores', 500
            

        
        new_action = DBAction(timestamp, 'results')
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
            awt = sum([r.time for r in class_results if (r.position > 0 and r.position <=3)]) / 3.0
            
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
                indv_class = indv_class.strip()
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
                team = TeamResult(event, c.class_code, team, score, True)
                db.session.add(team)
                db.session.commit()
    
        elif c.score_method == 'NOCI-team':
            indv_results = []
            for indv_class in c.team_classes.split('-'):
                indv_class = indv_class.strip()
                q = Result.query.filter_by(event=event).filter_by(class_code=indv_class).all()
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
                valid = True if contributors == 3 else False
                team = TeamResult(event, c.class_code, team, score, valid)
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
                        indv_class = indv_class.strip()
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
            team_results = TeamResult.query.filter_by(event=event, class_code=c.class_code, is_valid=True).all()
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
    
def _assignMultiScores(event):
    multi_classes = EventClass.query.filter_by(is_multi_scored=True).filter_by(event=event).all() #filter by event to only get ONE hit for each class.
    for c in multi_classes:
        if c.is_team_class:
            MultiResultTeam.query.filter_by(class_code=c.class_code).delete()
        else:
            MultiResultIndv.query.filter_by(class_code=c.class_code).delete()
        
        if c.multi_score_method == 'time-total':
            indv_results = Result.query.filter_by(class_code=c.class_code).order_by(Result.bib).all()
            if len(indv_results) == 0:
                continue
            individuals = _matchMultiResults(indv_results, [], [], lambda x,y: True if x.bib == y.bib else False)
            num_needed_scores = max([len(x) for x in individuals])
            for indv in individuals:
                score = 0
                valid = True
                for i in range(len(indv)):
                    if i == 0:
                        ids = str(indv[i].id)
                    else:
                        ids += '-{}'.format(indv[i].id)                                                
                    if indv[i].status == 'OK':
                        score += indv[i].time
                    else:
                        valid = False
                valid = True if (len(indv) == num_needed_scores) and valid else False
                new_multi_result = MultiResultIndv(c.class_code, score, ids, valid)
                db.session.add(new_multi_result)
            db.session.commit()
        
        elif c.multi_score_method == 'NOCI-multi':
            team_results = TeamResult.query.filter_by(class_code=c.class_code, is_valid=True).order_by(TeamResult.club_code).all()
            if len(team_results) == 0:
                continue
            teams = _matchMultiResults(team_results, [], [], lambda x,y: True if x.club_code == y.club_code else False)
            num_needed_scores = max([len(x) for x in teams])
            for team in teams:
                for i in range(len(team)):
                    if i == 0:
                        score = team[i].score
                        ids = str(team[i].id)
                    else:
                        score += team[i].score
                        ids += '-{}'.format(team[i].id)
                valid = True if len(team) == num_needed_scores else False
                new_multi_team = MultiResultTeam(c.class_code, score, ids, valid)
                db.session.add(new_multi_team)
            db.session.commit()

        else:
            pass
    return

def _matchMultiResults(input, same, output, matchf):
    if len(input) == 0:
        output.append(same)
        return output
    else:
        i = input.pop()
        if (len(same) == 0) or matchf(i, same[0]):
            same.append(i)
            return _matchMultiResults(input, same, output, matchf)
        else:
            output.append(same)
            same = [i]
            return _matchMultiResults(input, same, output, matchf)
        
def _assignMultiPositions(event):
    multi_classes = EventClass.query.filter_by(is_multi_scored=True).filter_by(event=event).all()
    for c in multi_classes:
        if c.multi_score_method == 'time-total':
            multi_results = MultiResultIndv.query.filter_by(class_code=c.class_code, is_valid=True).all()
            multi_results.sort(key=lambda x: x.score) # Low is better
            nextposition = 1
            for i in range(len(multi_results)):
                # if not multi_results[i].is_valid:
                    # multi_results[i].position = -1
                    # continue
                if i == 0:
                    multi_results[i].position = nextposition
                elif multi_results[i].score == multi_results[i-1].score:
                    multi_results[i].position == multi_results[i-1].position
                else:
                    multi_results[i].position = nextposition
                nextposition += 1
            db.session.add_all(multi_results)
            db.session.commit()
            
        if c.multi_score_method == 'NOCI-multi':
            multi_results = MultiResultTeam.query.filter_by(class_code=c.class_code, is_valid=True).all()
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