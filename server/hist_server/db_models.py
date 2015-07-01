#!/usr/bin/env python

from app import db


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    login = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))

    def __unicode__(self):
        return self.first_name


class Request(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    pattern = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    exemplar = db.Column(db.Integer, db.ForeignKey('histogram.id'))
    result = db.Column(db.Float)
    time = db.Column(db.DateTime)
    request_source = db.Column(db.String(64), db.ForeignKey('RequestType.id'))
    technique = db.Column(db.String(100), db.ForeignKey('technique.id'))

    def __unicode__(self):
        return self.id


class Histogram(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255))
    file_id = db.Column(db.String, db.ForeignKey('file.id'))
    pattern = db.relationship('Request', backref='pattern_name', primaryjoin='Request.pattern == Histogram.id')
    example = db.relationship('Request', backref='exemplar_name', primaryjoin='Request.exemplar == Histogram.id')

    def __str__(self):
        return self.path


class File(db.Model):

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    last_changes = db.Column(db.DateTime)
    path = db.Column(db.String(255))
    hist = db.relationship('Histogram', backref='file_name', lazy='dynamic')

    def __str__(self):
        return self.path


class RequestType(db.Model):

    __tablename__ = 'RequestType'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(64))
    requests_type_relation = db.relationship('Request', backref='request_typ', lazy='dynamic')

    def __str__(self):
        return self.type


class Technique(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    technique_relation = db.relationship('Request', backref='used_technique', lazy='dynamic')

    def __unicode__(self):
        return self.name
