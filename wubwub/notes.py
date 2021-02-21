#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:53 2021

@author: earnestt1234
"""

from itertools import cycle, chain

from wubwub.errors import WubWubError
from wubwub.resources import random_choice_generator

class Note:
    def __init__(self, pitch, length=1, volume=0):
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

class ArpChord:
    def __init__(self, notes, length):
        self.notes = notes
        self.length = length

    def __repr__(self):
        pitches = [note.pitch for note in self.notes]

        s = f'ArpChord(pitches={pitches}, length={self.length})'
        return s

def arpeggio_generator(notes, method):
    methods = ['up', 'down', 'updown', 'downup', 'up&down', 'down&up',
               'random']
    if method not in methods:
        formatted = ', '.join(m for m in methods)
        raise WubWubError(f'method must be in {formatted}')

    if method == 'up':
        return cycle(notes)
    if method == 'down':
        return cycle(notes[::-1])
    if method == 'updown':
        return cycle(chain(notes, notes[-2:0:-1]))
    if method == 'downup':
        return cycle(chain(notes[::-1], notes[1:-1]))
    if method == 'up&down':
        return cycle(chain(notes, notes[::-1]))
    if method == 'down&up':
        return cycle(chain(notes[::-1], notes))
    if method == 'random':
        return random_choice_generator(notes)

def arpeggiate(chord, beat, freq=0.5, method='up', chord_length='max'):

    notes = chord.notes

    if isinstance(chord, ArpChord):
        length = chord.length

    elif isinstance(chord, Chord):
        choices = {'min':min, 'max':max}
        length = choices[chord_length]([note.length for note in notes])

    else:
        raise WubWubError('chord must be wubwub.Chord or wubwub.ArpChord')

    current = beat
    end = beat + length
    arpeggiated = {}
    gen = arpeggio_generator(notes, method)

    while current < end:
        note = next(gen)
        length = freq if current + freq <= end else end-current
        arpeggiated[current] = Note(pitch=note.pitch, length=length, volume=note.volume)
        current += freq

    return arpeggiated

def chordify(a, b):
    if hasattr(a, 'notes'):
        a = list(a.notes)
    else:
        a = [a]
    if hasattr(b, 'notes'):
        b = list(b.notes)
    else:
        b = [b]

    return Chord(a + b)


