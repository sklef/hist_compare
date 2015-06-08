#!/usr/bin/env python

import utils
import db_models
import json
import flask_admin as admin

from flask import render_template, request


def compare():
    try:
        # Readings Request Parameters
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        request_type = request.args['type']
        technique = request.args['technique']

        request_type_id = utils.get_request_type_id(request_type)
        technique_id = utils.get_technique_id(technique)
        first_file_id = utils.get_file_id(base_hist_location)
        second_file_id = utils.get_file_id(cur_hist_location)
        first_histogram_id = utils.get_histogram_id(all_paths, first_file_id)
        second_histogram_id = utils.get_histogram_id(all_paths, second_file_id)
        # Check if query already exists
        previous_request = db_models.Request.query.filter_by(pattern=first_histogram_id,
                                                             exemplar=second_histogram_id,
                                                             technique=technique).order_by(db_models.Request.time).all()
        if previous_request:
            utils.previous_request_processing(previous_request[-1])
        else:
            distance = utils.hist_checking(base_hist_location, cur_hist_location, all_paths, technique)
        utils.save_request_result(first_histogram_id, second_histogram_id,
                                  request_type_id, technique_id, distance)
        return json.dumps({'rc': 0, 'message': '', 'distance': distance})
    except Exception, error_message:
        return json.dumps({'rc': 1, 'distance': None, 'message': str(error_message)})


def check():
    try:
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        technique = request.args['technique']

        first_histogram_id = utils.get_histogram_id(all_paths, base_hist_location)
        second_histogram_id = utils.get_histogram_id(all_paths, cur_hist_location)
        previous_request = db_models.Request.query.filter_by(pattern=first_histogram_id,
                                                             exemplar=second_histogram_id, technique=technique).all()
        if previous_request:
            return json.dumps({'time':previous_request.time})
        else:
            return json.dumps({'time':None})
    except Exception, error_message:
        return json.dumps({'message': str(error_message)})


# Flask views
def index():
    return render_template('index.html')


class AdminIndexView(admin.AdminIndexView):

    @admin.expose('/')
    def index(self):
        return super(AdminIndexView, self).index()