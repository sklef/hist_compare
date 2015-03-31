#!/usr/bin/env python
from flask import Flask, request
from rootpy.io import root_open

app = Flask(__name__)

@app.route('/compare')
def compare():
    base_hist = request.args['base_hist']
    cur_hist = request.args['cur_hist']
    all_paths = request.args['paths']
    base_file = root_open(base_hist)
    cur_file = root_open(cur_hist)
    cur_hist = cur_file.get(all_paths.encode('ascii','ignore'))
    base_hist = cur_file.get(all_paths.encode('ascii','ignore'))
    s = cur_hist.KolmogorovTest(base_hist)
    return str(s)

if __name__ == '__main__':
    app.run(debug=False)