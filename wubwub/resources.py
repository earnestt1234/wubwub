#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
General functions/constants used by wubwub.
"""

import random

SECOND = 1000
MINUTE = 60 * SECOND

def random_choice_generator(x):
    '''Generate repeated random choices from `x`.'''
    while True:
        yield random.choice(x)

def unique_name(base, others):
    '''Generate a new name, checked against a list of names.'''
    c = 1
    name = base + str(c)
    while name in others:
        name = base + str(c)
        c += 1
    return name
