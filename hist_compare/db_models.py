#!/usr/bin/env python

from api import db

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    login = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.first_name


class Request(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    pattern = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    exemplar = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    result = db.Column(db.Float)
    time = db.Column(db.DateTime)
    request_source = db.Column(db.String(64), db.ForeignKey('RequestType.id'))
    technique = db.Column(db.String(100), db.ForeignKey('technique.name'))

    def __unicode__(self):
        return self.id


class Histogram(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255))
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    pattern = db.relationship('Request', backref='pattern_name', primaryjoin='Request.pattern == Histogram.id')
    example = db.relationship('Request', backref='exemplar_name', primaryjoin='Request.exemplar == Histogram.id')

    def __unicode__(self):
        return self.path


class File(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    md5_hash = db.Column(db.String(64))
    path = db.Column(db.String(255))
    hist = db.relationship('Histogram', backref='file_name', lazy='dynamic')

    def __unicode__(self):
        return self.path


class RequestType(db.Model):

    __tablename__ = 'RequestType'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64))
    requests_type_relation = db.relationship('Request', backref='request_typ', lazy='dynamic')

    def __unicode__(self):
        return self.type


class Technique(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    technique_relation = db.relationship('Request', backref='used_technique', lazy='dynamic')

    def __unicode__(self):
        return self.name
