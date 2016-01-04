from flask import Blueprint, request, abort, render_template

from .models import db, Result
from OutilsParse import getRunners


resultsAPI = Blueprint("resultsAPI", __name__)

@resultsAPI.route('/', methods=['GET', 'POST'])
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

        #re-calculate everything (?) - no this happens at query time? nope, need some to happen now
        try:
            _assignPositions()
        except:
            return 'Problem assigning positions', 500

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

@resultsAPI.route('/clubs', methods=['GET', 'POST'])
def clubs():
    """do stuff here to upload club code to club name reference, and provide some reasbable view"""
    pass
