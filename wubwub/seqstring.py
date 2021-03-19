#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 22:50:31 2021

@author: earnestt1234
"""

import numpy as np

from wubwub.errors import WubWubError

def seqstring(sequencer, name_cutoff=None, singlenote='■', multinote='■', empty='□'):
    tracknames = []
    namelengths = []
    for track in sequencer.tracks():
        n = track.name
        if name_cutoff and len(track.name) > name_cutoff:
            n = track.name[:-4] + '...'

        tracknames.append(n)
        namelengths.append(len(n))

    namespacing = max(namelengths) + 1
    beatspacing = len(str(sequencer.beats)) + 1

    s = ''
    beat_header = ''.join([str(i+1).rjust(beatspacing) for i in range(sequencer.beats)])
    beat_header = ' ' * namespacing + beat_header
    s += beat_header + '\n'


    for name, track in zip(tracknames, sequencer.tracks()):
        s += name.rjust(namespacing)
        beatcount = track.count_by_beat()
        for i in range(sequencer.beats):
            count = beatcount.get(i + 1, -1)
            symbol = multinote
            if count == 1:
                symbol = singlenote
            if count == -1:
                symbol = empty
            s += symbol.rjust(beatspacing)
        s += '\n'

    return s

def seqstring2(sequencer, name_cutoff=None, resolution=1, singlenote='■',
               multinote='■', empty='□', wrap=32):
    tracknames = []
    namelengths = []
    for track in sequencer.tracks():
        n = track.name
        if name_cutoff and len(track.name) > name_cutoff:
            n = track.name[:-4] + '...'

        tracknames.append(n)
        namelengths.append(len(n))

    if (1 / resolution) * resolution != 1:
        raise WubWubError('`resolution` must evenly divide 1')

    steps = int(sequencer.beats * (1 / resolution))
    beats = np.linspace(1, sequencer.beats + 1, steps, endpoint=False)

    namespacing = max(namelengths) + 1
    beatspacing = len(str(sequencer.beats)) + 1

    chunks = [beats[i:i + wrap] for i in range(0, len(beats), wrap)]
    strings = []

    for i, chunk in enumerate(chunks):
        s = ''
        labelbeats = (chunk == chunk.astype(int))
        labels = np.where(labelbeats,
                          chunk.astype(int).astype(str),
                          '')

        beat_header = ''.join([j.rjust(beatspacing) for j in labels])
        beat_header = ' ' * namespacing + beat_header
        s += beat_header

        if i != len(chunks) - 1:
            s += '    \\'

        s += '\n'

        for name, track in zip(tracknames, sequencer.tracks()):
            s += name.rjust(namespacing)
            noteslice = track.ns()

            for beat in chunk:
                count = len(noteslice[beat:beat + resolution])
                symbol = multinote
                if count == 1:
                    symbol = singlenote
                if count == 0:
                    symbol = empty
                s += symbol.rjust(beatspacing)

            s += '\n'

        s += '\n'
        strings.append(s)

    return ''.join(strings).strip('\n')