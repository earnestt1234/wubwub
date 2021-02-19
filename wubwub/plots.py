#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:34:36 2021

@author: earnestt1234
"""

import matplotlib.pyplot as plt

def waveform(audiosegment):
    pass

import matplotlib.pyplot as plt

a = x.build().get_array_of_samples()



bins = 125
perbin = len(a) // bins
binned = [a[i:i+perbin] for i in range(0, len(a), perbin)]

mini_maxi = [(min(i), max(i)) for i in binned]
h = [i[1]-i[0] for i in mini_maxi]
bottom = [-i/2 for i in h]

fig, ax = plt.subplots(figsize=(30,10))
ax.bar(x=range(len(h)), height=h, bottom=bottom, width=0.5)
lo, hi = ax.get_ylim()
biggest = max(abs(lo), abs(hi))
ax.set_ylim(-biggest, biggest)