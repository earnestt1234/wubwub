#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:34:36 2021

@author: earnestt1234
"""

import matplotlib.pyplot as plt

from wubwub.resources import MINUTE

prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']

def sequencer_plot(sequencer, timesig=None):
    fig, ax = plt.subplots()
    ax.yaxis.grid(True, which='major')
    ax.xaxis.grid(True, which='major')

    mpb = 1 / sequencer.bpm * MINUTE

    yticks = []
    ylabs = []
    for y, track in enumerate(sequencer.tracks()):
        color = colors[y]
        beats = track.array_of_beats()
        notes = track.array_of_notes()

        ax.scatter(beats, [-y] * len(beats), color=color, zorder=5)
        yticks.append(-y)
        ylabs.append(track.name)

        for b, n in zip(beats, notes):
            l = getattr(n, 'length', False)
            if l is False:
                l = max(note.length for note in l.notes)
            samplelength = len(track.sample) / mpb
            l = min(l, samplelength)
            ax.plot([b, b+l], [-y, -y], color=color)

    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabs)




#%%
# a = x.build().get_array_of_samples()



# bins = 125
# perbin = len(a) // bins
# binned = [a[i:i+perbin] for i in range(0, len(a), perbin)]

# mini_maxi = [(min(i), max(i)) for i in binned]
# h = [i[1]-i[0] for i in mini_maxi]
# bottom = [-i/2 for i in h]

# fig, ax = plt.subplots(figsize=(30,10))
# ax.bar(x=range(len(h)), height=h, bottom=bottom, width=0.5)
# lo, hi = ax.get_ylim()
# biggest = max(abs(lo), abs(hi))
# ax.set_ylim(-biggest, biggest)