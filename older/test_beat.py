#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 21 17:14:40 2021

@author: earnestt1234
"""

import array
from collections.abc import Iterable
from collections import deque
import itertools
import random
import re

import numpy as np
import pandas as pd
import pydub
from pydub.playback import play
from pysndfx import AudioEffectsChain
from sortedcontainers import SortedDict

SECOND = 1000
MINUTE = 60 * SECOND
NOTES = ['C' , 'C#', 'Db', 'D' , 'D#', 'Eb', 'E' , 'F', 'F#',
         'Gb', 'G' , 'G#', 'Ab', 'A' , 'A#', 'Bb', 'B',]
NOTES_JOIN = '|'.join(NOTES)
DIFF =  [0   , 1   , 1   , 2   , 3   , 3   , 4   , 5   , 6   ,
         6   , 7   , 8   , 8   , 9   , 10  , 10  , 11  ]
DIFF_DEQUE = deque(DIFF)
DIFFDF = pd.DataFrame(index=NOTES, columns=NOTES,)

for i in DIFFDF.index:
    DIFFDF.loc[i] = DIFF_DEQUE
    DIFF_DEQUE.rotate(1)

def randomgen(x):
    while True:
        yield random.choice(x)

def valid_pitch_str(s):
    pattern = f"^({NOTES_JOIN})[0-9]$"
    return bool(re.match(pattern, s))

def relative_pitch_to_int(a, b):
    pitch_a, octave_a = splitoctave(a)
    pitch_b, octave_b = splitoctave(b)
    octave_diff = octave_b - octave_a
    pitch_diff = DIFFDF.loc[pitch_a, pitch_b]
    return pitch_diff + (12 * octave_diff)

def splitoctave(pitch_str, octave_type=int):
    if not valid_pitch_str(pitch_str):
        raise WubWubError(f'"{pitch_str}" is not a valid pitch string')
    return pitch_str[:-1], octave_type(pitch_str[-1])

def shift_pitch(sound, semitones):
    octaves = (semitones/12)
    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    new_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    new_sound = new_sound.set_frame_rate(44100)
    return new_sound

def add_effects(sound, fx):
    samples = np.array(sound.get_array_of_samples())
    samples = fx(samples)
    samples = array.array(sound.array_type, samples)
    effected = sound._spawn(samples)
    return effected

def add_note_to_audio(note, audio, sample, position, duration, basepitch):
    pitch = note.pitch
    if isinstance(pitch, str):
        pitch = relative_pitch_to_int(basepitch, pitch)
    sound = sample if pitch == 0 else shift_pitch(sample, pitch)
    sound += note.volume
    sound = sound[:duration]
    audio = audio.overlay(sound, position=position)
    return audio

class Note:
    def __init__(self, beat, pitch, duration, volume):
        self.beat = beat
        self.pitch = pitch
        self.duration = duration
        self.volume = volume

class Chord:
    def __init__(self, beat, pitches, duration, volume):
        self.beat = beat
        self.pitches = pitches
        self.duration = duration
        self.volume = volume

class TrackSection:
    def __init__(self, track, name, length):
        self.track = track
        self.name = name
        self.notes = SortedDict()
        self.length = length

    def add_notes(self, beat, pitch=0, length=1, volume=0,
                  pitch_select='cycle', length_select='cycle',
                  volume_select='cycle'):

        if not isinstance(beat, Iterable):
            beat = [beat]

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        for b in beat:
            self.notes[b] = Note(b, next(pitch), next(length), next(volume))

    def add_notes_every(self, freq, offset=0, pitch=0, length=1, volume=0,
                        pitch_select='cycle', length_select='cycle',
                        volume_select='cycle'):

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        b = 1 + offset
        while b < self.length + 1:
            self.notes[b] = Note(b, next(pitch), next(length), next(volume))
            b += freq

    def render(self, effects=False):
        b = (1/self.track.beat.bpm) * MINUTE
        audio = pydub.AudioSegment.silent(duration=self.length * b)
        sample = self.track.sample
        basepitch = self.track.basepitch
        for beat, note in self.notes.items():
            position = (beat-1) * b
            duration = note.duration * b
            audio = add_note_to_audio(note=note,
                                      audio=audio,
                                      sample=sample,
                                      position=position,
                                      duration=duration,
                                      basepitch=basepitch)
        if effects and self.track.effects:
            audio = add_effects(audio, self.track.effects)
        return audio

    def play(self, rerender=True):
        play(self.render(effects=True))


    def _convert_select_arg(self, arg, option):
        if not isinstance(arg, Iterable) or isinstance(arg, str):
            arg = [arg]

        if option == 'cycle':
            return itertools.cycle(arg)
        elif option == 'random':
            return randomgen(arg)
        else:
            raise WubWubError('pitch, length, and volume select must be ',
                              '"cycle" or "random".')

class Track:
    def __init__(self, beat, sample, overlap=True, basepitch='C4'):
        self.beat = beat
        self.sample = pydub.AudioSegment.from_wav(sample)
        self.overlap = overlap
        self.basepitch = basepitch
        self.effects = None

        self.sections = SortedDict()
        for num, beatsection in self.beat.sections.items():
            self.sections[num] = TrackSection(track=self,
                                              name=beatsection.name,
                                              length=beatsection.length)
        self.working_section = self.sections.values()[0]

    def add_notes(self, beat, pitch=0, length=1, volume=0,
                  pitch_select='cycle', length_select='cycle',
                  volume_select='cycle'):
        self.working_section.add_notes(beat=beat,
                                       pitch=pitch,
                                       length=length,
                                       volume=volume,
                                       pitch_select=pitch_select,
                                       length_select=length_select,
                                       volume_select=volume_select)

    def add_notes_every(self, freq, offset=0, pitch=0, length=1, volume=0,
                        pitch_select='cycle', length_select='cycle',
                        volume_select='cycle'):

        self.working_section.add_notes_every(freq=freq,
                                             offset=offset,
                                             pitch=pitch,
                                             length=length,
                                             volume=volume,
                                             pitch_select=pitch_select,
                                             length_select=length_select,
                                             volume_select=volume_select)

    def render(self, section=None):
        b = (1/self.beat.bpm) * MINUTE
        if section is None:
            length = self.beat.total_length
            audio = pydub.AudioSegment.silent(duration=length * b)
            offset = 0
            for num, tracksection in self.sections.items():
                r = tracksection.render()
                audio = audio.overlay(r, position=offset*b)
                offset = tracksection.length
        else:
            pass
        if self.effects is not None:
            audio = add_effects(audio, self.effects)
        return audio

    def play(self, rerender=True):
        play(self.render())

class BeatSection:
    def __init__(self, beat, name, length):
        self.beat = beat
        self.name = name
        self.length = length

class Beat:
    def __init__(self, bpm=120, sections=1, length=16):
        self.bpm = bpm

        self.sections = SortedDict()
        for i in range(1, sections+1):
            self.sections[i] = BeatSection(beat=self,
                                           name=f'Section {i}',
                                           length=length)
        self.total_length = sum(i.length for i in self.sections.values())

        self.audio = None
        self.tracks = SortedDict()

    def add_track(self, sample, name=None, overlap=True, basepitch='C4'):
        new = Track(beat=self, sample=sample, overlap=overlap,
                    basepitch=basepitch)
        if name is None:
            base = "Track"
            c = 1
            while name in self.tracks or name is None:
                name = base + str(c)
                c += 1
        self.tracks[name] = new
        return new

    def render(self):
        b = (1/self.bpm) * MINUTE
        self.audio = pydub.AudioSegment.silent(duration=self.total_length * b)
        for track in self.tracks.values():
            self.audio = self.audio.overlay(track.render())
        return self.audio

    def play(self, rerender=True):
        play(self.render())

class WubWubError(Exception):
    """Class for wubwub errors."""

x = Beat(bpm=100, length=8, sections=2)
hihat = x.add_track('808/hi hat (1).wav')
snare = x.add_track('808/snare (1).wav')
kick = x.add_track('808/kick (11).wav')
synth = x.add_track('trumpet.wav')
hihat.add_notes_every(1/4)
snare.add_notes_every(2, 1)
kick.add_notes_every(1)
synth.add_notes([1, 3, 5, 7], pitch=[0, 8, 3, 7], length=2)

fx = AudioEffectsChain().reverb()
hihat.effects=fx
synth.effects=fx

x.play()