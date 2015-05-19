import logic
import db_models
import json
import flask_admin as admin

from flask import render_template, request
from api import app


# Flask views
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare')
def compare():
    try:
        # Request Parameters Reading
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        request_type = request.args['type']
        technique = request.args['technique']

        request_type_id = logic.get_request_type_id(request_type)
        technique_id = logic.get_technique_id(technique)
        first_file_id = logic.get_file_id(base_hist_location)
        second_file_id = logic.get_file_id(cur_hist_location)
        first_histogram_id = logic.get_histogram_id(first_file_id, all_paths)
        second_histogram_id = logic.get_histogram_id(second_file_id, all_paths)
        # Check if query already exists
        previous_request = db_models.Request.query.filter_by(pattern=first_histogram_id,
                                                   exemplar=second_histogram_id, technique=technique).all()
        if previous_request:
            logic.previous_request_processing(previous_request[-1])
        else:
            distance = logic.hist_checking(base_hist_location, cur_hist_location, all_paths, technique)
        logic.save_request_result(first_histogram_id, second_histogram_id,
                            request_type_id, technique_id, distance)
        return json.dumps({'rc': 0, 'message': '', 'distance': distance})
    except Exception, error_message:
        return json.dumps({'rc': 1, 'distance': None, 'message': error_message})


@app.route('/check')
def check():
    try:
        base_hist_location = request.args['base_hist']
        cur_hist_location = request.args['cur_hist']
        all_paths = request.args['paths']
        technique = request.args['technique']

        first_histogram_id = logic.get_histogram_id(all_paths, base_hist_location)
        second_histogram_id = logic.get_histogram_id(all_paths, cur_hist_location)
        previous_request = db_models.Request.query.filter_by(pattern=first_histogram_id,
                                                   exemplar=second_histogram_id, technique=technique).all()
        if previous_request:
            return json.dumps({'time':previous_request.time})
        else:
            return json.dumps({'time':None})
    except Exception, error_message:
        return json.dumps({'message': error_message})


class AdminIndexView(admin.AdminIndexView):

    @admin.expose('/')
    def index(self):
        return super(AdminIndexView, self).index()