#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 14:34:36 2021

@author: earnestt1234
"""
from numbers import Number

import matplotlib as mpl
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
        ax = plt.gca()
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
        notes = track.notedict.values()

        ax.scatter(beats, [-y] * len(beats), color=color, marker=marker,
                   zorder=5, **scatter_kwds)
        yticks.append(-y)
        ylabs.append(track.name)

        for b, n in zip(beats, notes):
            clss = n.__class__.__name__
            l = getattr(n, 'length', False)
            if l is False:
                l = max(note.length for note in n.notes)
            if clss != 'ArpChord':
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

    return ax.figure

def _convert_semitones_str_yaxis(plottype, note, track):
    if plottype == 'semitones' and isinstance(note.pitch, str):
        return relative_pitch_to_int(track.basepitch, note.pitch)
    elif plottype == 'pitch' and isinstance(note.pitch, Number):
        return pitch_from_semitones(track.basepitch, note.pitch)
    else:
        return note.pitch

def _format_pitch_yaxis(ax, pitchnums, max_range=24, max_pitches=12):
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
        ax = plt.gca()
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

    for beat, element in track.notedict.items():

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

    return ax.figure

def draw_pianoroll(ax, lo, hi, notenames=True):
    lo_num = relative_pitch_to_int('C1', lo) - 2
    hi_num = relative_pitch_to_int('C1', hi) + 2
    num_notes = hi_num - lo_num
    if 14 < num_notes < 20:
        fontsize = 8
    if num_notes >= 20:
        notenames = False
    else:
        fontsize = 10

    ax.set_xlim(0, 1)
    ax.set_ylim(lo_num, hi_num+1)

    black = [1, 3, 6, 8, 10]
    for i in range(lo_num, hi_num+1):
        facecolor = 'black' if i % 12 in black else 'white'
        rect = mpl.patches.Rectangle((0, i), width=1, height=1, facecolor=facecolor,
                                     edgecolor='black')
        ax.add_patch(rect)
        if notenames:
            note = pitch_from_semitones('C1', i)
            textcolor = {'white':'black', 'black':'white'}[facecolor]
            ax.text(0.1, i + 0.5, note, color=textcolor, va='center', fontsize=fontsize)

def pianoroll(track, timesig=4, grid=True,):

    fig = plt.figure()
    gs = fig.add_gridspec(1, 10)
    plt.subplots_adjust(wspace=0)

    ax0 = fig.add_subplot(gs[:, 1])
    ax1 = fig.add_subplot(gs[:, 2:], sharey=ax0)
    ax1.set_xlabel('beats')
    ax0.set_ylabel('pitch')

    beats = []
    notes = []
    lengths = []
    mpb = 1 / track.get_bpm() * MINUTE

    for beat, element in track.notedict.items():

        clss = element.__class__.__name__

        if clss == "Note":
            beats.append(beat)
            notes.append(_convert_semitones_str_yaxis('pitch', element, track))
            lengths.append(_actual_soundlength(element.length, track.sample, mpb))

        if clss == 'Chord':
            for note in element.notes:
                beats.append(beat)
                notes.append(_convert_semitones_str_yaxis('pitch', note, track))
                lengths.append(_actual_soundlength(note.length, track.sample, mpb))

        if clss == 'ArpChord':
            for note in element.notes:
                beats.append(beat)
                notes.append(_convert_semitones_str_yaxis('pitch', note, track))
                lengths.append(element.length)

    semitones = [relative_pitch_to_int('C1', n) for n in notes]
    lo = notes[semitones.index(min(semitones))]
    hi = notes[semitones.index(max(semitones))]
    draw_pianoroll(ax0, lo, hi)
    ax1.set_xlim(1, track.get_beats() + 1)

    for b, n, l in zip(beats, semitones, lengths):
        rect = mpl.patches.Rectangle((b, n), width=l, height=1, color='firebrick', alpha=.7)
        ax1.add_patch(rect)

    ax0.set_xticks([])
    ax1.set_yticklabels([])
    for tic in ax0.yaxis.get_major_ticks():
            tic.tick1line.set_visible(False)
    for tic in ax1.yaxis.get_major_ticks():
        tic.tick1line.set_visible(False)
    if grid:
        ax1.set_yticks(range(min(semitones)-2, max(semitones)+3))
        ax1.yaxis.grid(True, which='major', alpha=.3)
        ax1.xaxis.grid(True, which='major', alpha=.3)
        ax1.xaxis.grid(which='minor', alpha=.3)

    return fig
