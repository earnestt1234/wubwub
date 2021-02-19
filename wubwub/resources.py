#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:26 2021

@author: earnestt1234
"""

import random

SECOND = 1000
MINUTE = 60 * SECOND

def random_choice_generator(x):
    while True:
        yield random.choice(x)