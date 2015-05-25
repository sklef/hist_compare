#!/usr/bin/env python

import requests
from collections import namedtuple
import sys


data_to_compare = namedtuple('data_to_compare', 'base_hist, cur_hist, path')


HOST_NAME = 'http://localhost:5000/compare'
ALL_FILE_NAMES = []
ALL_HISTS = []

def hist_compare(first_file, second_file, all_paths, technique=u'Kolmogorov-Smirnov'):
    all_pvalues = []
    for path in all_paths:
        payload = {'base_hist': first_file , 'cur_hist': second_file, 'paths': path,
                   'technique': technique, 'type': 'User'}
        result = requests.get(HOST_NAME, params=payload).text
        all_pvalues.append(result)
    return all_pvalues


def check_histograms(data_locations):
    payload = {'base_hist': data_locations.base_hist,
               'cur_hist': data_locations.cur_hist,
               'paths': data_locations.path}
    result = requests.get(HOST_NAME, params=payload).text
    if


if __name__ == '__main__':
    first_file = 'default_1.root'
    second_file = 'default_1.root'
    all_paths = ['Timing/OverallEventProcTime/overallTime']
    print hist_compare(first_file, second_file, all_paths)
