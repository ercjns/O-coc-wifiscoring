from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class RemotePunch(db.Model):
    __tablename__ = 'wifiscoring_remotepunch'

    id = db.Column(db.Integer, primary_key=True)
    station = db.Column(db.Integer)
    SIcard = db.Column(db.Integer)
    time = db.Column(db.Time)
    
    def __init__(self, station, SIcard, time):
        self.station = station
        self.SIcard = SIcard
        self.time = time

    def __repr__(self):
        return '<Punch at {:d} by {:d}>'.format(self.station, self.SIcard)

    def __str__(self):
        return 'At {} -> {:d} punched box #{:d}'.format(self.time, self.SIcard, self.station)