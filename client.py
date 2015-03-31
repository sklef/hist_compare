#!/usr/bin/env python
import requests

HOST_NAME = 'http://localhost:5000/compare'

def hist_compare(first_file, second_file, all_paths):
    all_pvalues = []
    for path in all_paths:
        payload = {'base_hist': first_file , 'cur_hist': second_file, 'paths': path }
        result = requests.get(HOST_NAME, params=payload).text
        message = ""
        try:
            distance = float(result)
            rc = 0
            struct = {'rc': rc, 'distance': distance, 'message': message}
            all_pvalues.append(struct)
        except ValueError:
            message = result
            rc  = 1
            struct = {'rc': rc, 'message': message}
            all_pvalues.append(struct)
    return all_pvalues

if __name__ == '__main__':
    first_file = 'default_1.root'
    second_file = 'default_1.root'
    all_paths = ['Timing/OverallEventProcTime/overallTime']
    print hist_compare(first_file, second_file, all_paths)