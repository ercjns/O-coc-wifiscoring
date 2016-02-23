from flask import Blueprint, request, abort, render_template
from datetime import datetime

from .models import db, Result, Club, Cclass, TeamResult, Entry, Action
from OutilsParse import getRunners

import ETL as ETL


API = Blueprint("resultsAPI", __name__)

@API.route('/results', methods=['GET', 'POST'])
def results():
    if request.method == 'GET':
        #try:
        q = Result.query.all()
        return render_template('basiclist.html', items=q)
        #except:
        #abort(404)

    elif request.method == 'POST':
        try:
            request.files[request.files.keys()[0]].save('latestResultsXML.xml')
        except:
            return 'Please upload an IOF XML ResultsList', 400

        try:
            results = getRunners('latestResultsXML.xml')
        except:
            return 'GetRunners failed. :(', 500

        #TODO: implement a primary/secondary db swap scheme
        try:
            Result.query.delete()
            TeamResult.query.delete()
        except:
            return 'couldn\'t delete things', 500
        
        try:
            for r in results:
                result_dict = { 'sicard': int(r.estick if r.estick>0 else -1),
                                'name': str(r.name),
                                'cclassshort': str(r.cclass),
                                'clubshort': str(r.club),
                                'time': int(r.time if r.time>0 else -1),
                                'status': str(r.status),
                                'position': int(r.position if r.position>0 else -1)
                              }
                new_result = Result(result_dict)
                db.session.add(new_result)
                db.session.commit()
        except:
            return 'Problem building up the db refresh', 500

        try:
            _assignPositions()
            _assignScores('COC')
            
        except:
            return 'Problem assigning positions or scores', 500
        
        _assignTeamScores('WIOL')
        _assignTeamPositions('WIOL')
        #TODO: calculate team scores
        new_action = Action(datetime.now(), 'results')
        db.session.add(new_action)
        db.session.commit()
        return 'Refreshed', 200

def _assignPositions():
    cclasses = db.session.query(Result.cclassshort.distinct()).all()
    for c in cclasses:
        classresults = Result.query.filter_by(cclassshort=c[0]).filter_by(status="OK").order_by(Result.time).all()
        nextposition = 1
        for i in range(len(classresults)):
            if i == 0:
                classresults[i].position = nextposition
            elif classresults[i].time == classresults[i-1].time:
                classresults[i].position = classresults[i-1].position
            else:
                classresults[i].position = nextposition
            nextposition += 1
            
        db.session.add_all(classresults)
        db.session.commit()
    return

def _assignScores(algo):
    cclasses = db.session.query(Result.cclassshort.distinct()).all()
    for c in cclasses:
        if not Cclass.query.filter_by(cclassshort=c[0]).all()[0].isScored:
            continue
        
        classresults = Result.query.filter_by(cclassshort=c[0]).order_by(Result.position).all()
        
        if algo is 'COC':
            for r in classresults:
                if r.position is -1:
                    if r.status in ['DidNotFinish', 'MissingPunch', 'Disqualified']:
                        r.score = 0
                    else:
                        r.score = None
                elif r.position == 1:
                    r.score = 100
                elif r.position == 2:
                    r.score = 95
                elif r.position == 3:
                    r.score = 92
                else:
                    r.score = 100 - 6 - int(r.position)

        elif algo is 'ISOC':
            awt = sum([r.time for r in classresults if r.position <=3]) / 3.0
            for r in classresults:
                if r.status in ['OK']:
                    r.score = 60*r.time / awt
                elif r.status in ['DidNotFinish', 'MissingPunch', 'Disqualified', 'Overtime']:
                    #TODO: need faster awt of male and female classes here.
                    r.score = 10 + 60*(3*60*60) / awt
                else:
                    r.score = None
        
        db.session.add_all(classresults)
        db.session.commit()
    return

def _assignTeamScores(algo):
    if algo is 'WIOL':
        WIOL_team_classes = ['W2', 'W3F', 'W4M', 'W5M', 'W6F', 'W6M']
        for c in WIOL_team_classes:
            if c is 'W2':
                classresults = Result.query.filter_by(cclassshort='W2M').all()
                classresults += Result.query.filter_by(cclassshort='W2F').all()
            else:
                classresults = Result.query.filter_by(cclassshort=c).all()

            classteams = set([r.clubshort for r in classresults])

            for club in classteams:
                score = 0
                contributors = 0
                clubmembers = [r for r in classresults if ((r.clubshort == club) and r.score)]
                clubmembers.sort(key=lambda x: -x.score)

                while (len(clubmembers) > 0) and (contributors < 3):
                    scorer = clubmembers.pop(0)
                    score += scorer.score
                    scorer.isTeamScorer = True
                    contributors += 1
                    db.session.add(scorer)

                if clubmembers:
                    for nonscorer in clubmembers:
                        nonscorer.isTeamScorer = False

                    db.session.add_all(clubmembers)

                team = TeamResult(c, club, score)
                db.session.add(team)
                db.session.commit()
                
    elif algo is 'ISOC':
        #IS_classes = ['ISVM', 'ISVF', 'ISJVM', 'ISJVF', 'ISIM', 'ISIF', 'ISPM', 'ISPF']
        #IS_team_classes = ['ISV', 'ISJV', 'ISI']
        # TODO: determine how meet classes will be set up. Faking with WIOL for now.
        IS_team_classes = {'ISV':['W6M', 'W6F'], 'JV':['W3F','W4M', 'W5M'], 'ISI':['W2F','W2M']}
        for IS_team_class, IS_ind_classes in IS_team_classes.items():
            classresults = []
            for c in IS_ind_classes:
                classresults += Result.query.filter_by(cclassshort=c).all()
            classteams = set([r.clubshort for r in classresults])
            
            for team in classteams:
                team_members = [r for r in classresults if (r.clubshort == team)]
                team_members.sort(key=lambda x: x.score)
                score = 0
                for i in range(len(team_members)):
                    if i < 3:
                        try:
                            score += team_members[i].score
                            team_members[i].isTeamScorer = True
                        except TypeError:
                            score += 1000 # for a "none" score - flag something wrong
                            team_members[i].isTeamScorer = False
                    else:
                        team_members[i].isTeamScorer = False
                        
                if len(team_members) < 3:
                    score += 5000 # for a team smaller than 3 - flag something wrong
                        
                team_result = TeamResult(IS_team_class, team, score)
                
                db.session.add_all(team_members)
                db.session.add(team_result)
                db.session.commit()

    return

def _assignTeamPositions(algo):
    if algo is 'WIOL':
        TeamResults = TeamResult.query.all()
        for c in set([team.cclassshort for team in TeamResults]):
            classteams = [t for t in TeamResults if t.cclassshort == c]
            classteams.sort(key=lambda x: -x.score)

            nextposition = 1
            for i in range(len(classteams)):
                if i == 0:
                    classteams[i].position = nextposition
                elif classteams[i].score < classteams[i-1].score:
                    classteams[i].position = nextposition
                else: 
                    a = classteams[i-1]
                    b = classteams[i]
                    runnerclasses = [c]
                    if c == 'W2':
                        runnerclasses = ['W2F', 'W2M']
                    
                    a_scorers = []
                    b_scorers = []
                    for rc in runnerclasses:
                        a_scorers += Result.query.filter_by(cclassshort=rc, clubshort=a.clubshort, isTeamScorer=True).all()
                        b_scorers += Result.query.filter_by(cclassshort=rc, clubshort=b.clubshort, isTeamScorer=True).all()
                        
                    a_scorers.sort(key=lambda x: -x.score)
                    b_scorers.sort(key=lambda x: -x.score)
                    
                    for j in range(3):
                        try:
                            tiebreakerA = a_scorers[j].score
                        except IndexError:
                            tiebreakerA = 0
                        try:
                            tiebreakerB = b_scorers[j].score
                        except IndexError:
                            tiebreakerB = 0
                        if tiebreakerA > tiebreakerB:
                            b.position = nextposition
                            break
                        elif tiebreakerB > tiebreakerA:
                            b.position = a.position
                            a.position = nextposition
                            break
                        else:
                            continue
                    if b.position == None: 
                        b.position = a.position
                nextposition += 1

            db.session.add_all(classteams)
            db.session.commit()
            
    elif algo is 'ISOC':
        TeamResults = TeamResult.query.all()
        for c in set([team.cclassshort for team in TeamResults]):
            category_teams = [t for t in TeamResults if t.cclassshort == c]
            category_teams.sort(key=lambda x: x.score)
            nextposition = 1
            for i in range(len(category_teams)):
                if i == 0:
                    category_teams[i].position = nextposition
                elif category_teams[i].score == category_teams[i-1].score:
                    category_teams[i].position = category_teams[i-1].position
                else:
                    category_teams[i].position = nextposition
                nextposition += 1
            
            db.session.add_all(category_teams)
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
            abbr = club['abbr']
            full = club['name']
            q = Club.query.filter_by(clubshort=abbr).all()
            
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
        

@API.route('/classes', methods=['GET', 'PUT', 'DELETE'])
def cclasses():
    """ Mapping of class code to full name
    
    GET returns a view of all classes
    PUT accepts a list of classes and will update data
    DELETE will clear the entire collection
    """
    
    if request.method == 'GET':
        q = Cclass.query.all()
        return render_template('basiclist.html', items=q)

        
    elif request.method == 'PUT':
        f = request.files[request.files.keys()[0]]
        cclasses = ETL.cclassjson(f)
        
        for cclass in cclasses:
            abbr = cclass['abbr']
            full = cclass['name']
            public = bool(cclass['public'])
            scored = bool(cclass['scored'])
            
            q = Cclass.query.filter_by(cclassshort=abbr).all()
            
            if len(q) > 2:
                return 'Internal Error: Multiple clubs found for ' + abbr, 500
                
            if not q:
                new_cclass = Cclass(abbr, full, public, scored)
                db.session.add(new_cclass)
                
            elif q:
                existing_cclass = q[0]
                edit = False
                if existing_cclass.cclassfull != full:
                    existing_cclass.cclassfull = full
                    edit = True
                if existing_cclass.isPublic != public:
                    existing_cclass.isPublic = public
                    edit = True
                if existing_cclass.isScored != scored:
                    existing_cclass.isScored = scored
                    edit = True
                if edit:
                    db.session.add(existing_cclass)
                    
        db.session.commit()
        return 'Competition Class table updated', 200

    elif request.method == 'DELETE':
        pass
        
@API.route('/entries', methods=['GET','PUT'])
def entries():
    """ Name to class and SIcard mapping
    
    GET returns evertyhing
    PUT accepts an iof3 XML entries list and updates data
    DELETE clears the collection
    """
    if request.method == 'GET':
        q = Entry.query.all()
        return render_template('basiclist.html', items=q)
        
    if request.method == 'PUT':
        request.files[request.files.keys()[0]].save('entries.xml')
        entries = ETL.entriesXML3('entries.xml')
        for e in entries:
            new_entry = Entry(e['name'], e['cclass'], e['club'], e['sicard'])
            db.session.add(new_entry)
        db.session.commit()
        return 'Updated Entries', 200