#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:10:34 2021

@author: earnestt1234
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
import itertools
from numbers import Number
import os

import numpy as np
import pprint
import pydub
from pydub.playback import play
from sortedcontainers import SortedDict

from wubwub.audio import add_note_to_audio, add_effects
from wubwub.errors import WubWubError
from wubwub.notes import Note, Chord, arpeggiate
from wubwub.resources import random_choice_generator, MINUTE

class Track(metaclass=ABCMeta):
    def __init__(self, name, sample, manager, basepitch='C4'):
        self.basepitch = basepitch
        self.effects = None

        self.notes = SortedDict()
        self.samplepath = None
        self._manager = manager
        if self not in self._manager.tracks:
            self._manager.add_track(self)
        self._name = None
        self._sample = None
        self.name = name
        self.sample = sample

    def __repr__(self):
        return f'GenericTrack(name="{self.name}", sample="{self.samplepath}")'

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

    def get_bpm(self):
        return self._manager._sequencer.bpm

    def get_beats(self):
        return self._manager._sequencer.beats

    def get_sequencer(self):
        return self._manager._sequencer

    def pprint_notes(self):
        pprint.pprint(self.notes)

    def unpack_notes(self):
        unpacked = []
        for b, element in self.notes.items():
            if isinstance(element, Note):
                unpacked.append((b, element))
            elif isinstance(element, Chord):
                for note in element.notes:
                    unpacked.append((b, note))
        return unpacked

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def play(self):
        pass

class Sampler(Track):
    def __init__(self, name, sample, manager, basepitch='C4', overlap=True):
        super().__init__(name, sample, manager, basepitch)
        self.overlap = overlap

    def __repr__(self):
        return f'SamplerTrack(name="{self.name}", sample="{self.samplepath}")'

    def new_notes(self, beat, pitch=0, length=1, volume=0,
                  pitch_select='cycle', length_select='cycle',
                  volume_select='cycle'):

        if not isinstance(beat, Iterable):
            beat = [beat]

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        for b in beat:
            self.notes[b] = Note(next(pitch), next(length), next(volume))

    def new_notes_every(self, freq, offset=0, pitch=0, length=1, volume=0,
                        pitch_select='cycle', length_select='cycle',
                        volume_select='cycle'):

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        b = 1 + offset
        while b < self.get_beats() + 1:
            self.notes[b] = Note(next(pitch), next(length), next(volume))
            b += freq

    def new_chord(self, beat, pitches, lengths=1, volumes=0):

        if not isinstance(beat, Iterable):
            beat = [beat]

        if not isinstance(pitches, Iterable) or isinstance(pitches, str):
            pitches = [pitches]

        if isinstance(lengths, Number):
            lengths = [lengths] * len(pitches)

        if isinstance(volumes, Number):
            volumes = [volumes] * len(pitches)

        notes = [Note(p, l, v) for p, l, v in zip(pitches, lengths, volumes)]

        for b in beat:
            self.notes[b] = Chord(notes)

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
        next_position = np.inf
        for beat, value in sorted(self.notes.items(), reverse=True):
            position = (beat-1) * b
            if isinstance(value, Note):
                note = value
                duration = note.length * b
                if (position + duration) > next_position and not self.overlap:
                    duration = next_position - position
                next_position = position
                audio = add_note_to_audio(note=note,
                                          audio=audio,
                                          sample=sample,
                                          position=position,
                                          duration=duration,
                                          basepitch=basepitch)
            elif isinstance(value, Chord):
                chord = value
                for note in chord.notes:
                    duration = note.length * b
                    if (position + duration) > next_position and not self.overlap:
                        duration = next_position - position
                    audio = add_note_to_audio(note=note,
                                              audio=audio,
                                              sample=sample,
                                              position=position,
                                              duration=duration,
                                              basepitch=basepitch)
                next_position = position


        if self.effects:
            audio = add_effects(audio, self.effects)
        return audio

    def play(self, overhang=0, overhang_type='beats'):
        play(self.build(overhang, overhang_type))

class Arpeggiator(Track):
    def __init__(self, name, sample, manager, basepitch='C4', freq=.5,
                 method='up'):
        super().__init__(name, sample, manager, basepitch)
        self.freq = freq
        self.method = method

    def new_arpeggio(self, beat, pitches, length=1):
        pitches = sorted(pitches)
        notes = [Note(p, length=length, volume=0) for p  in pitches]

        self.notes[beat] = Chord(notes)

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
        next_beat = np.inf
        for beat, chord in sorted(self.notes.items(), reverse=True):
            length = max(note.length for note in chord.notes)
            if beat + length > next_beat:
                length = next_beat - beat
            next_beat = beat
            arpeggiated = arpeggiate(chord, beat=beat, length=length,
                                     freq=self.freq, method=self.method)
            for arpbeat, note in arpeggiated.items():
                position = (arpbeat-1) * b
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

    def add_track(self, track):
        self.tracks.append(track)

    def delete_track(self, track):
        if isinstance(track, Track):
            self.tracks.remove(track)
        elif isinstance(track, str):
            self.tracks.remove(self.get_track(track))