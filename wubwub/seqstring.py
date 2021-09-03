#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 22:50:31 2021

@author: earnestt1234
"""

import numpy as np

from wubwub.errors import WubWubError

def seqstring(sequencer, name_cutoff=None, resolution=1, singlenote='■',
              multinote='■', empty='□', wrap=32):
    tracknames = []
    namelengths = []
    for track in sequencer.tracks():
        n = track.name
        if name_cutoff and len(track.name) > name_cutoff:
            n = track.name[:-4] + '...'

        tracknames.append(n)
        namelengths.append(len(n))

    if ((1 / resolution) % 1) != 0:
        raise WubWubError('`resolution` must evenly divide 1')

    steps = int(sequencer.beats * (1 / resolution))
    beats = np.linspace(1, sequencer.beats + 1, steps, endpoint=False)

    namespacing = max(namelengths)
    beatspacing = len(str(sequencer.beats)) + 1

    chunks = [beats[i:i + wrap] for i in range(0, len(beats), wrap)]
    strings = []

    boxarray = np.zeros((len(sequencer.tracks()), steps))

    for i, track in enumerate(sequencer.tracks()):
        unpacked = track.unpack_notes()
        for beat, note in unpacked:
            start = int((beat-1) // resolution)
            boxarray[i, start] += 1

    boxarray[boxarray > 2] = 2
    conversiondict = {0 : empty,
                      1 : singlenote,
                      2 : multinote}

    idx = 0
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

        for j, (name, track) in enumerate(zip(tracknames, sequencer.tracks())):
            s += name.rjust(namespacing)
            arraysection = boxarray[j, idx:idx+len(chunk)]
            s += ''.join(conversiondict[a].rjust(beatspacing)
                         for a in arraysection)

            s += '\n'

        s += '\n'
        strings.append(s)
        idx += len(chunk)

    return ''.join(strings).strip('\n')



