from flask import Blueprint, request, abort, render_template

from .models import db, Result, Club, Cclass
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
        #get the file from the request body
        try:
            request.files[request.files.keys()[0]].save('latestResultsXML.xml')
        except:
            return 'Please upload an IOF XML ResultsList', 400

        #pass the file to getRunners
        try:
            results = getRunners('latestResultsXML.xml')
        except:
            return 'GetRunners failed. :(', 500

        #wipe the database
        #TODO: implement a primary/secondary db swap scheme
        try:
            Result.query.delete()
        except:
            return 'couldn\'t delete things', 500

        #take the list of runners and create new db entries
        # try:
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
        # except:
            # return 'Problem adding rows to the db', 500

        #calculate places
        try:
            _assignPositions()
        except:
            return 'Problem assigning positions', 500
            
        #TODO: calculate points and team scores

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