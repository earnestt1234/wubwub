#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:26 2021

@author: earnestt1234
"""

import random

import numpy as np

SECOND = 1000
MINUTE = 60 * SECOND

def random_choice_generator(x):
    while True:
        yield random.choice(x)

def unique_name(base, others):
    c = 1
    name = base + str(c)
    while name in others:
        name = base + str(c)
        c += 1
    return name

def repeated_measures(beats, measurelen=4, measures=2):
    beats = np.array(beats)
    output = np.empty(0)
    while measures:
        output = np.append(output, beats)
        beats += measurelen
        measures -= 1

    return list(output)
