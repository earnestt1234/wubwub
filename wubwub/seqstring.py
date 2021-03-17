#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 16 22:50:31 2021

@author: earnestt1234
"""

def seqstring(sequencer, name_cutoff=None, singlenote='X', multinote='M', empty=' '):
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