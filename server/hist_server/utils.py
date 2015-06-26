#!/usr/bin/env python

import hashlib
import os.path, time
import datetime
from rootpy.io import root_open
from app import db
from db_models import Histogram, File, Request, RequestType, Technique, User
from werkzeug.security import generate_password_hash
HASH_CHUNK_SIZE = 256


def md5_sum_calculation(file_name):
    hash_values = hashlib.md5()
    with open(file_name, 'r') as file_object:
        # Iterating over small chunks of file
        for chunk in iter(lambda: file_object.read(HASH_CHUNK_SIZE), ''):
            hash_values.update(chunk)
    return hash_values.hexdigest()


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def get_file_id(file_path):
    file_query = File.query.filter_by(path=file_path).all()
    if not file_query:
        new_hist_file = File(path=file_path,
                             last_changes=modification_date(file_path))
        db.session.add(new_hist_file)
        db.session.flush()
        file_id= new_hist_file.id
    elif len(file_query) > 1:
        raise ValueError('Two identical files in database')
    else:
        file_id = file_query[0].id
    return file_id


def get_histogram_id(hist_path, file_id):
    histogram_query = Histogram.query.filter_by(file_id=file_id, path=hist_path).all()
    if not histogram_query:
        new_hist_object = Histogram(path=hist_path, file_id=file_id)
        db.session.add(new_hist_object)
        db.session.flush()
        histogram_id = new_hist_object.id
    elif len(histogram_query) > 1:
        raise ValueError('Two identical histograms in database')
    else:
        histogram_id = histogram_query[0].id
    return histogram_id


def get_request_type_id(request_type):
    request_type = RequestType.query.filter_by(type=request_type).all()
    if not request_type:
        raise ValueError('No Such Request Type')
    elif len(request_type) > 1:
        raise ValueError('Two identical request types')
    else:
        request_type_id = request_type[0].id
    return request_type_id


def get_technique_id(technique_name):
    request_technique = Technique.query.filter_by(name=technique_name).all()
    if not request_technique:
        raise ValueError("No such technique")
    elif len(request_technique) > 1:
        raise ValueError("Two identical techniques")
    else:
        technique_id = request_technique[0].id
    return technique_id


def save_request_result(first_histogram_id, second_histogram_id,
                        request_type_id, technique_id, distance):
    new_request = Request()
    new_request.pattern = first_histogram_id
    new_request.exemplar = second_histogram_id
    new_request.time = db.func.now()
    new_request.request_source = request_type_id
    new_request.technique = technique_id
    new_request.result = distance
    db.session.add(new_request)
    db.session.commit()


def previous_request_processing(last_request):
    first_hist = Histogram.query.get(last_request.pattern)
    second_hist = Histogram.query.get(last_request.exemplar)
    technique_id = last_request.technique
    technique = Technique.query.get(technique_id)
    first_file_id = first_hist.file_id
    second_file_id = second_hist.file_id
    first_file = File.query.get(first_file_id)
    second_file = File.query.get(second_file_id)
    control_hist_location = first_file.path
    cur_hist_location = second_file.path
    path = first_hist.path

    pattern_file = File.query.filter_by(id=first_file_id).first()
    pattern_file_location = pattern_file.path
    pattern_file_last_changes = pattern_file.last_changes
    pattern_current_last_changes = modification_date(pattern_file_location)(pattern_file_location)
    exemplar_file = File.query.filter_by(id=second_file_id).first()
    exemplar_last_changes = exemplar_file.last_changes
    exemplar_file_location = exemplar_file.path
    exemplar_current_last_changes = modification_date(exemplar_file_location)(exemplar_file_location)
    # Update modification dates
    if (pattern_file_last_changes == pattern_current_last_changes
        and exemplar_last_changes == exemplar_current_last_changes):
        distance = last_request.result
    else:
        hist_checking(control_hist_location, cur_hist_location, path, technique)
        distance = last_request.result
    return distance


def hist_checking(control_hist_location, cur_hist_location, path, technique):
    with root_open(control_hist_location) as control_file, \
            root_open(cur_hist_location) as cur_file:
        cur_hist = cur_file.get(path.encode('ascii','ignore'))
        control_hist = control_file.get(path.encode('ascii','ignore'))
        if technique == 'Kolmogorov-Smirnov':
            p_value = cur_hist.KolmogorovTest(control_hist)
        elif technique == 'chi_square':
            p_value = cur_hist.Chi2Test(control_hist)
    return 1. - p_value


def build_sample_db():
    db.create_all()
    db.drop_all()
    db.create_all()
    user = User()
    user.first_name = 'admin'
    user.last_name = 'admin'
    user.login = 'admin'
    user.email = user.login + "@example.com"
    user.password = generate_password_hash('admin')
    db.session.add(user)
    db.session.add(RequestType(type='User'))
    db.session.add(RequestType(type='Bot'))
    db.session.add(Technique(name='chi_square'))
    db.session.add(Technique(name='Kolmogorov-Smirnov'))
    db.session.commit()