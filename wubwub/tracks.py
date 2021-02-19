#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:10:34 2021

@author: earnestt1234
"""

from collections.abc import Iterable
import itertools
import os

import pydub
from pydub.playback import play
from sortedcontainers import SortedDict

from wubwub.audio import add_note_to_audio, add_effects
from wubwub.errors import WubWubError
from wubwub.notes import Note, Chord
from wubwub.resources import random_choice_generator, MINUTE

class Track:
    def __init__(self, name, sample, manager, overlap=True, basepitch='C4'):
        self.overlap = overlap
        self.basepitch = basepitch
        self.effects = None

        self._notes = SortedDict()
        self.samplepath = None
        self._manager = manager
        self._name = None
        self._sample = None
        self.name = name
        self.sample = sample

    def __repr__(self):
        return f'Track(name="{self.name}", sample="{self.samplepath}")'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new):
        if new in self._manager.get_tracknames():
            raise WubWubError(f'track name "{new}" already in use.')
        self._name = new

    @property
    def sample(self):
        return self._sample

    @sample.setter
    def sample(self, sample):
        if isinstance(sample, str):
            self._sample = pydub.AudioSegment.from_wav(sample)
            self.samplepath = os.path.abspath(sample)
        elif isinstance(sample, pydub.AudioSegment):
            self._sample = sample
        else:
            raise WubWubError('sample must be a path or pydub.AudioSegment')

    def new_notes(self, beat, pitch=0, length=1, volume=0,
                  pitch_select='cycle', length_select='cycle',
                  volume_select='cycle'):

        if not isinstance(beat, Iterable):
            beat = [beat]

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        for b in beat:
            self._notes[b] = Note(b, next(pitch), next(length), next(volume))

    def new_notes_every(self, freq, offset=0, pitch=0, length=1, volume=0,
                        pitch_select='cycle', length_select='cycle',
                        volume_select='cycle'):

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        b = 1 + offset
        while b < self.get_beats() + 1:
            self._notes[b] = Note(b, next(pitch), next(length), next(volume))
            b += freq

    def _convert_select_arg(self, arg, option):
        if not isinstance(arg, Iterable) or isinstance(arg, str):
            arg = [arg]

        if option == 'cycle':
            return itertools.cycle(arg)
        elif option == 'random':
            return random_choice_generator(arg)
        else:
            raise WubWubError('pitch, length, and volume select must be ',
                              '"cycle" or "random".')

    def get_bpm(self):
        return self._manager._sequencer.bpm

    def get_beats(self):
        return self._manager._sequencer.beats

    def get_sequencer(self):
        return self._manager._sequencer

    def notes(self):
        return tuple(self._notes.values())

    def build(self, overhang=0, overhang_type='beats'):
        b = (1/self.get_bpm()) * MINUTE
        if overhang_type == 'beats':
            overhang = b * overhang
        elif overhang_type in ['s', 'seconds']:
            overhang = overhang * 1000
        else:
            raise WubWubError('overhang must be "beats" or "s"')
        tracklength = self.get_beats() * b + overhang
        audio = pydub.AudioSegment.silent(duration=tracklength)
        sample = self.sample
        basepitch = self.basepitch
        for beat, note in self._notes.items():
            position = (beat-1) * b
            duration = note.length * b
            audio = add_note_to_audio(note=note,
                                      audio=audio,
                                      sample=sample,
                                      position=position,
                                      duration=duration,
                                      basepitch=basepitch)
        if self.effects:
            audio = add_effects(audio, self.effects)
        return audio

    def play(self, overhang=0, overhang_type='beats'):
        play(self.build(overhang, overhang_type))

class TrackManager:
    def __init__(self, sequencer):
        self._sequencer = sequencer
        self.tracks = []

    def get_track(self, name):
        try:
            return next(t for t in self.tracks if t.name == name)
        except:
            raise ValueError(f'no track with name {name}')

    def get_tracknames(self):
        return [t.name for t in self.tracks]

    def new_track(self, name, sample, overlap=True, basepitch='C4'):
        new = Track(name=name, sample=sample, manager=self,
                    overlap=overlap, basepitch=basepitch)
        self.tracks.append(new)
        return new

    def delete_track(self, track):
        if isinstance(track, Track):
            self.tracks.remove(track)
        elif isinstance(track, str):
            self.tracks.remove(self.get_track(track))