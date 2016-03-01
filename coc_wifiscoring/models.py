from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String)
    sicard = db.Column(db.Integer)
    name = db.Column(db.String)
    class_code = db.Column(db.String)
    club_code = db.Column(db.String)
    
    def __init__(self, event, name, cclassshort, club=None, sicard=None):
        self.event = event
        self.name = name
        self.class_code = cclassshort
        self.club_code = club
        self.sicard = sicard

    def __repr__(self):
        return '<Entry {} on {}>'.format(self.name, self.class_code)

    def __str__(self):
        return '{}'.format(self.name)


class EventClass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String)
    class_code = db.Column(db.String)
    class_name = db.Column(db.String)
    is_scored = db.Column(db.Boolean)
    score_method = db.Column(db.String)
    is_multi_scored = db.Column(db.Boolean)
    multi_score_method = db.Column(db.String)
    is_team_class = db.Column(db.Boolean)
    team_classes = db.Column(db.String)
    
    def __init__(self, event, classinfo):
        self.event = event
        self.class_code = classinfo['class_code']
        self.class_name = classinfo['class_name']
        self.is_scored = classinfo['is_scored']
        self.score_method = classinfo['score_method']
        self.is_multi_scored = classinfo['is_multi_scored']
        self.multi_score_method = classinfo['multi_score_method']
        self.is_team_class = classinfo['is_team_class']
        self.team_classes = classinfo['team_classes']
        return

    def __repr__(self):
        return '<Course {} - {}>'.format(self.class_code, self.class_name)

    def __str__(self):
        return '{}'.format(self.class_name)


class Club(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    club_code = db.Column(db.String)
    club_name = db.Column(db.String)
    
    def __init__(self, short, long):
        self.club_code = short
        self.club_name = long

    def __repr__(self):
        return '<Club Object - {}>'.format(self.club_code)

    def __str__(self):
        return '{} ({})'.format(self.club_name, self.club_code)


class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String)
    sicard = db.Column(db.Integer)
    bib = db.Column(db.Integer)
    name = db.Column(db.String)
    class_code = db.Column(db.String)
    club_code = db.Column(db.String)
    time = db.Column(db.Integer)
    status = db.Column(db.String)
    position = db.Column(db.Integer)
    score = db.Column(db.Float)
    team_id = db.Column(db.Integer)
    is_team_scorer = db.Column(db.Boolean)
    multi_id = db.Column(db.Integer)

    def __init__(self, event, result_dict):
        self.event = event
        self.sicard = result_dict['sicard']
        self.name = result_dict['name']
        self.bib = result_dict['bib']
        self.class_code = result_dict['class_code']
        self.club_code = result_dict['club_code']
        self.time = result_dict['time']
        self.status = result_dict['status']
        
        return
        
    def __repr__(self):
        return '<Result Object - sicard {}>'.format(self.sicard)

    def __str__(self):
        return 'Result for {} ({}) in class {}: {}'.format(self.name, self.sicard, self.class_code, self.time)

    def timetommmss(self):
        if (self.time == None) or (self.time == -1):
            return '--:--'
        minutes, seconds = divmod(self.time, 60)
        m, s = str(minutes), str(seconds)
        if len(s) < 2:
            s = "0" + s
        return m + ":" + s
        
    def score2f(self):
        return '{:.2f}'.format(self.score)

        
class TeamResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String)
    club_code = db.Column(db.String)
    class_code = db.Column(db.String)
    position = db.Column(db.Integer)
    score = db.Column(db.Float)
    is_valid = db.Column(db.Boolean)
    multi_id = db.Column(db.Integer)
    
    def __init__(self, event, cclass, club, score, valid):
        self.event = event
        self.class_code = cclass
        self.club_code = club
        self.score = score
        self.is_valid = valid
        return
    
    def __repr__(self):
        return '<TeamResult for {} in {}>'.format(self.club_code, self.class_code)
        
    def __str__(self):
        return 'Team {} in position {} on {} with a score of {}'.format(self.club_code, self.position, self.class_code, self.score)
        
    def score2f(self):
        return '{:.2f}'.format(self.score)


class MultiResultIndv(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String)
    score = db.Column(db.Integer)
    is_valid = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    result_ids = db.Column(db.String)
    
    def __init__(self, class_code, score, ids, valid):
        self.class_code = class_code
        self.score = score
        self.result_ids = ids
        self.is_valid = valid
        return

    def scoreasmmmss(self):
        # For individual multi-score as total time, store time as seconds, format as below
        minutes, seconds = divmod(self.score, 60)
        m, s = str(minutes), str(seconds)
        if len(s) < 2:
            s = "0" + s
        return m + ":" + s
    
    
class MultiResultTeam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String)
    score = db.Column(db.Integer)
    is_valid = db.Column(db.Boolean)
    position = db.Column(db.Integer)
    result_ids = db.Column(db.String)

    def __init__(self, class_code, score, ids, valid):
        self.class_code = class_code
        self.score = score
        self.result_ids = ids
        self.is_valid = valid
        return

    def score2f(self):
        return '{:.2f}'.format(self.score)
        
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_code = db.Column(db.String)
    event_name = db.Column(db.String)
    date = db.Column(db.String)
    venue = db.Column(db.String)
    description = db.Column(db.String)
    
    def __init__(self, code, name, date, venue, description=None):
        self.event_code = code
        self.event_name = name
        self.date = date
        self.venue = venue
        self.description = description
        return

class RemotePunch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String)
    station = db.Column(db.Integer)
    sicard = db.Column(db.Integer)
    time = db.Column(db.Time)

    def __init__(self, station, sicard, time):
        self.station = station
        self.sicard = sicard
        self.time = time

    def __repr__(self):
        return '<Punch at {:d} by {:d}>'.format(self.station, self.sicard)

    def __str__(self):
        return 'At {} -> {:d} punched box #{:d}'.format(self.time, self.sicard, self.station)

   
class DBAction(db.Model):
    __tablename__ = 'wifiscoring_actions'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    action = db.Column(db.String)
    
    def __init__(self, time, action):
        self.time = time
        self.action = action

