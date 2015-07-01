#!/usr/bin/env python

import requests
from collections import namedtuple


data_to_compare = namedtuple('data_to_compare', 'control_hist, cur_hist, path')


#HOST_NAME = 'http://localhost:5000/compare'
HOST_NAME = 'http://hist03:5000/compare'
ALL_FILE_NAMES = []
ALL_HISTS = []


def hist_compare(first_file, second_file, all_paths, technique=u'Kolmogorov-Smirnov'):
    all_pvalues = []
    for path in all_paths:
        payload = {'control_hist': first_file , 'cur_hist': second_file, 'paths': path,
                   'technique': technique, 'type': 'User'}
        result = requests.get(HOST_NAME, params=payload).text
        all_pvalues.append(result)
    return all_pvalues



if __name__ == '__main__':
    first_file = '/home/austyuzh/root/default_1.root'
    second_file = '/home/austyuzh/root/BrunelDaVinci_FULL_134363_00021387.root'
#    first_file = 'default_1.root'
#    second_file = 'BrunelDaVinci_FULL_134363_00021387.root'
    all_paths = ['Timing/OverallEventProcTime/overallTime']
    print hist_compare(first_file, second_file, all_paths)
