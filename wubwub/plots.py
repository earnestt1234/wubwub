#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:34:36 2021

@author: earnestt1234
"""
from numbers import Number

import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

from wubwub.errors import WubWubError
from wubwub.pitch import pitch_from_semitones, relative_pitch_to_int
from wubwub.resources import MINUTE

prop_cycle = plt.rcParams['axes.prop_cycle']
colors = prop_cycle.by_key()['color']

def sequencerplot(sequencer, timesig=4, grid=True, ax=None, scatter_kwds=None,
                  plot_kwds=None):
    if ax is None:
        fig, ax = plt.subplots()
    if scatter_kwds is None:
        scatter_kwds = {}
    if plot_kwds is None:
        plot_kwds = {}

    if grid:
        ax.yaxis.grid(True, which='major', alpha=.3)
        ax.xaxis.grid(True, which='major', alpha=.3)
        ax.xaxis.grid(which='minor', alpha=.3)
    ax.set_ylabel('tracks')
    ax.set_xlabel('beats')

    mpb = 1 / sequencer.bpm * MINUTE

    yticks = []
    ylabs = []
    c = 0
    for y, track in enumerate(sequencer.tracks()):
        color = track.plotting.get('color')
        marker =  track.plotting.get('marker')

        if not color:
            color = colors[c]
            c += 1
        if not marker:
            marker = 'o'

        beats = track.array_of_beats()
        notes = track.notes.values()

        ax.scatter(beats, [-y] * len(beats), color=color, marker=marker,
                   zorder=5, **scatter_kwds)
        yticks.append(-y)
        ylabs.append(track.name)

        for b, n in zip(beats, notes):
            l = getattr(n, 'length', False)
            if l is False:
                l = max(note.length for note in n.notes)
            samplelength = len(track.sample) / mpb
            l = min(l, samplelength)
            ax.plot([b, b+l], [-y, -y], color=color, **plot_kwds)

    max_beats = sequencer.beats + 1
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabs)
    beat_range = max_beats
    ax.set_xlim(0.5, beat_range + 0.5)

    step = 1
    xticks = range(1, max_beats+1, step)
    c = 1
    while len(xticks) > 10:
        step = timesig * c
        xticks = range(1, max_beats+1, step)
        c += 1
    ax.set_xticks(xticks)
    minor_locator = AutoMinorLocator(2)
    ax.xaxis.set_minor_locator(minor_locator)

def _convert_semitones_str_yaxis(plottype, note, track):
    if plottype == 'semitones' and isinstance(note.pitch, str):
        return relative_pitch_to_int(track.basepitch, note.pitch)
    elif plottype == 'pitch' and isinstance(note.pitch, Number):
        return pitch_from_semitones(track.basepitch, note.pitch)
    else:
        return note.pitch

def _format_pitch_yaxis(ax, pitchnums, max_range=24, max_pitches=12):
    # names = [pitch_from_semitones('C1', p) for p in pitchnums]
    lo = min(pitchnums)
    hi = max(pitchnums)
    pitchrange = hi - lo
    if pitchrange > max_range or len(pitchnums) > max_pitches:
        yticks = [i for i in range(lo, hi) if i % 12 == 0]
    else:
        yticks = list(pitchnums)
    labels = [pitch_from_semitones('C1', y) for y in yticks]
    ax.set_yticks(yticks)
    ax.set_yticklabels(labels)

def _actual_soundlength(beatlength, sample, mpb):
    samplelength = len(sample) / mpb
    return min(beatlength, samplelength)

def trackplot(track, yaxis='semitones', timesig=4, grid=True, ax=None):
    if yaxis not in ['pitch', 'semitones']:
        raise WubWubError('yaxis must be "pitch" or "semitones".')
    if ax is None:
        fig, ax = plt.subplots()
    if grid:
        ax.yaxis.grid(True, which='major', alpha=.3)
        ax.xaxis.grid(True, which='major', alpha=.3)
        ax.xaxis.grid(which='minor', alpha=.3)
    ax.set_ylabel(yaxis)
    ax.set_xlabel('beats')


    mpb = 1 / track.get_bpm() * MINUTE
    pitchnums = set()

    color = track.plotting.get('color')
    marker =  track.plotting.get('marker')

    if not color:
        color = 'blue'
    if not marker:
        marker = 'o'

    beats = []
    notes = []
    lengths = []

    for beat, element in track.notes.items():

        clss = element.__class__.__name__

        if clss == "Note":
            beats.append(beat)
            notes.append(element)
            lengths.append(_actual_soundlength(element.length, track.sample, mpb))

        if clss == 'Chord':
            for note in element.notes:
                beats.append(beat)
                notes.append(note)
                lengths.append(_actual_soundlength(note.length, track.sample, mpb))

        if clss == 'ArpChord':
            for note in element.notes:
                beats.append(beat)
                notes.append(note)
                lengths.append(element.length)

    for b, n, l in zip(beats, notes, lengths):
        p = _convert_semitones_str_yaxis(yaxis, n, track)
        if isinstance(p, str):
            p = relative_pitch_to_int('C1', p)
            pitchnums.add(p)
        ax.scatter(b, p, color=color)

        ax.plot([b, b+l], [p, p], color=color)

    if yaxis == 'pitch':
        _format_pitch_yaxis(ax, pitchnums)

    max_beats = track.get_beats() + 1
    step = 1
    xticks = range(1, max_beats+1, step)
    c = 1
    while len(xticks) > 10:
        step = timesig * c
        xticks = range(1, max_beats+1, step)
        c += 1
    ax.set_xticks(xticks)
    minor_locator = AutoMinorLocator(2)
    ax.xaxis.set_minor_locator(minor_locator)









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