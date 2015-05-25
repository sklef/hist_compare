#!/usr/bin/env python

import hashlib
from rootpy.io import root_open
from api import db
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


def get_file_id(file_path):
        file_query = File.query.filter_by(path=file_path).all()
        if not file_query:
            new_hist_file = File(path=file_path,
                                 md5_hash=md5_sum_calculation(file_path))
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
    elif len(file_id) > 1:
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


def hist_checking(base_hist_location, cur_hist_location, path, technique):
    with root_open(base_hist_location) as base_file, \
            root_open(cur_hist_location) as cur_file:
        cur_hist = cur_file.get(path.encode('ascii','ignore'))
        base_hist = base_file.get(path.encode('ascii','ignore'))
        if technique == 'Kolmogorov-Smirnov':
            p_value = cur_hist.KolmogorovTest(base_hist)
        elif technique == 'Chi2Test':
            p_value = cur_hist.Chi2Test(base_file)
    return 1. - p_value


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
    base_hist_location = first_file.path
    cur_hist_location = second_file.path
    path = first_hist.path

    pattern_file = File.query.filter_by(id=first_file_id).first()
    pattern_file_location = pattern_file.path
    pattern_file_hash = pattern_file.md5_hash
    pattern_current_hash = md5_sum_calculation(pattern_file_location)
    exemplar_file = File.query.filter_by(id=second_file_id).first()
    exemplar_hash = exemplar_file.md5_hash
    exemplar_file_location = exemplar_file.path
    exemplar_current_hash = md5_sum_calculation(exemplar_file_location)
    # Update hashes if they have changed
    if (exemplar_hash == exemplar_current_hash
        and pattern_file_hash == pattern_current_hash):
        distance = last_request.result
    else:
        hist_checking(base_hist_location, cur_hist_location, path, technique)
        distance = last_request.result
    return distance


def hist_checking(base_hist_location, cur_hist_location, path, technique):
    with root_open(base_hist_location) as base_file, \
            root_open(cur_hist_location) as cur_file:
        cur_hist = cur_file.get(path.encode('ascii','ignore'))
        base_hist = base_file.get(path.encode('ascii','ignore'))
        if technique == 'Kolmogorov-Smirnov':
            p_value = cur_hist.KolmogorovTest(base_hist)
        elif technique == 'Chi2Test':
            p_value = cur_hist.Chi2Test(base_file)
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


