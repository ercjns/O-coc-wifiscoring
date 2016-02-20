from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RemotePunch(db.Model):
    __tablename__ = 'wifiscoring_remotepunch'

    id = db.Column(db.Integer, primary_key=True)
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
        
class Entry(db.Model):
    __tablename__ = 'wifiscoring_entry'

    id = db.Column(db.Integer, primary_key=True)
    sicard = db.Column(db.Integer)
    name = db.Column(db.String)
    cclassshort = db.Column(db.String)
    clubshort = db.Column(db.String)
    
    def __init__(self, name, cclassshort, club=None, sicard=None):
        self.name = name
        self.cclassshort = cclassshort
        self.club = club
        self.sicard = sicard

    def __repr__(self):
        return '<Entry {:s} on {:s}>'.format(self.name, self.cclassshort)

    def __str__(self):
        return '{:s}'.format(self.name)


class Cclass(db.Model):
    __tablename__ = 'wifiscoring_cclass'

    id = db.Column(db.Integer, primary_key=True)
    cclassshort = db.Column(db.String)
    cclassfull = db.Column(db.String)
    isPublic = db.Column(db.Boolean)
    isScored = db.Column(db.Boolean)
    
    def __init__(self, short, long, public, scored):
        self.cclassshort = short
        self.cclassfull = long
        self.isPublic = public
        self.isScored = scored

    def __repr__(self):
        return '<Course {:s} - {:s}>'.format(self.cclassshort, self.cclassfull)

    def __str__(self):
        return '{:s}'.format(self.cclassfull)


class Club(db.Model):
    __tablename__ = 'wifiscoring_club'

    id = db.Column(db.Integer, primary_key=True)
    clubshort = db.Column(db.String)
    clubfull = db.Column(db.String)
    
    def __init__(self, short, long):
        self.clubshort = short
        self.clubfull = long

    def __repr__(self):
        return '<Club {:s} - {:s}>'.format(self.clubshort, self.clubfull)

    def __str__(self):
        return '{:s} ({:s})'.format(self.clubfull, self.clubshort)


class Result(db.Model):
    __tablename__ = 'wifiscoring_result'

    id = db.Column(db.Integer, primary_key=True)
    sicard = db.Column(db.Integer)
    name = db.Column(db.String)
    cclassshort = db.Column(db.String)
    clubshort = db.Column(db.String)
    time = db.Column(db.Integer)
    status = db.Column(db.String)
    position = db.Column(db.Integer)
    score = db.Column(db.Float)
    isTeamScorer = db.Column(db.Boolean)

    def __init__(self, result_dict):
        self.sicard = result_dict['sicard']
        self.name = result_dict['name']
        self.cclassshort = result_dict['cclassshort']
        self.clubshort = result_dict['clubshort']
        self.time = result_dict['time']
        self.status = result_dict['status']
        self.position = result_dict['position']
        
    def __repr__(self):
        return '<Result in class {0} with sicard {1}>'.format(self.cclassshort, self.sicard)

    def __str__(self):
        return 'Result for {} ({}) in class {}: {}'.format(self.name, self.sicard, self.cclassshort, self.time)

    def timetommmss(self):
        if (self.time == None) or (self.time == -1):
            return '--:--'
        minutes, seconds = divmod(self.time, 60)
        m, s = str(minutes), str(seconds)
        if len(s) < 2:
            s = "0" + s
        return m + ":" + s
        
class TeamResult(db.Model):
    __tablename__ = 'wifiscoring_teamresult'
    
    id = db.Column(db.Integer, primary_key=True)
    clubshort = db.Column(db.String)
    cclassshort = db.Column(db.String)
    position = db.Column(db.Integer)
    score = db.Column(db.Float)
    
    def __init__(self, cclass, club, score):
        self.cclassshort = cclass
        self.clubshort = club
        self.score = score
    
    def __repr__(self):
        return '<TeamResult for {:s} in {:s}>'.format(self.clubshort, self.cclassshort)
        
    def __str__(self):
        return 'Team {} in position {} on {} with a score of {}'.format(self.clubshort, self.position, self.cclassshort, self.score)
    
TeamMembers = db.Table('wifiscoring_teammembers', 
    db.Column('result_id', db.Integer, db.ForeignKey('wifiscoring_result.id')), 
    db.Column('team_id', db.Integer, db.ForeignKey('wifiscoring_teamresult.id'))
)

class Action(db.Model):
    __tablename__ = 'wifiscoring_actions'
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    action = db.Column(db.String)
    
    def __init__(self, time, action):
        self.time = time
        self.action = action
