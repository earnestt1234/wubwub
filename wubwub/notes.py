#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:53 2021

@author: earnestt1234
"""

from collections.abc import Iterable
from itertools import cycle
from numbers import Number

from wubwub.errors import WubWubError

# class GenericNote:
#     def __init__(self):
#         pass
#     def __repr__(self):
#             attribs = ', '.join([str(k)+'='+str(v) for k, v in vars(self).items()])
#             return f'Note({attribs})'


class Note:
    def __init__(self, pitch, length, volume):
        self.pitch = pitch
        self.length = length
        self.volume = volume

    def __repr__(self):
        attribs = ', '.join([str(k)+'='+str(v) for k, v in vars(self).items()])
        return f'Note({attribs})'

class Chord:
    def __init__(self, notes):
        self.notes = notes

    def __repr__(self):
        pitches = []
        lengths = []
        volumes = []

        for note in self.notes:
            pitches.append(note.pitch)
            lengths.append(note.length)
            volumes.append(note.volume)

        s = f'Chord(pitches={pitches}, lengths={lengths}, volumes={volumes})'
        return s

def arpeggiate(chord, beat, length, freq=0.5, method='up'):
    current = beat
    end = beat + length
    arpeggiated = {}
    notes = sorted(chord.notes, key=lambda x: x.pitch)
    if method == 'up':
        gen = cycle(chord.notes)
    while current < end:
        note = next(gen)
        length = freq if current + freq <= end else end-current
        arpeggiated[current] = Note(pitch=note.pitch, length=length, volume=note.volume)
        current += freq
    return arpeggiated


