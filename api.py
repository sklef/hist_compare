#!/usr/bin/env python
from flask import Flask, request
from rootpy.io import root_open
import json

app = Flask(__name__)

@app.route('/compare')
def compare():
    try:
        base_hist = request.args['base_hist']
        cur_hist = request.args['cur_hist']
        all_paths = request.args['paths']
        base_file = root_open(base_hist)
        cur_file = root_open(cur_hist)
        cur_hist = cur_file.get(all_paths.encode('ascii','ignore'))
        base_hist = cur_file.get(all_paths.encode('ascii','ignore'))
        p_value = cur_hist.KolmogorovTest(base_hist)
        return json.dumps({'rc': 0, 'message': '', 'distance': 1 - p_value})
    except Exception, s:
        return json.dumps({'rc': 1, 'distance': '0', 'message': s})

if __name__ == '__main__':
    app.run(debug=False)