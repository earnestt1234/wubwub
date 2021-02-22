#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:53 2021

@author: earnestt1234
"""

from collections.abc import Iterable
from copy import copy
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

    def __add__(self, other):
        other = other.copy()
        if hasattr(other, 'notes'):
            other = list(other.notes)
        else:
            other = [other]
        return Chord([self.copy()] + other)

    def __radd__(self, other):
        if other == 0:
            return self.copy()
        else:
            return self.__add__(other)

    def copy(self):
        return Note(pitch=copy(self.pitch),
                    length=copy(self.length),
                    volume=copy(self.volume))

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

    def __getitem__(self, index):
        return self.notes[index]

    def __add__(self, other):
        other = other.copy()
        if hasattr(other, 'notes'):
            other = list(other.notes)
        else:
            other = [other]
        return Chord(list(self.copy().notes) + other)

    def __radd__(self, other):
        if other == 0:
            return self.copy()
        else:
            return self.__add__(other)

    def add(self, note, copy=True):
        if copy:
            note = note.copy()
        self.notes.append(note)

    def copy(self):
        return Chord([note.copy() for note in self.notes])

class ArpChord(Chord):
    def __init__(self, notes, length):
        super().__init__(notes)
        self.length = length

    def __repr__(self):
        pitches = [note.pitch for note in self.notes]

        s = f'ArpChord(pitches={pitches}, length={self.length})'
        return s

    def __add__(self, other):
        other = other.copy()
        if hasattr(other, 'notes'):
            other = list(other.notes)
        else:
            other = [other]
        return ArpChord([self.copy().notes] + other)

    def __radd__(self, other):
        if other == 0:
            return self.copy()
        else:
            return self.__add__(other)

    def copy(self):
        return ArpChord([note.copy() for note in self.notes], self.length)

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

def arpeggiate(chord, beat, length=None, freq=0.5, method='up', auto_chord_length='max'):

    notes = chord.notes

    if length is None:
        if isinstance(chord, ArpChord):
            length = chord.length

        elif isinstance(chord, Chord):
            choices = {'min':min, 'max':max}
            length = choices[auto_chord_length]([note.length for note in notes])

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
