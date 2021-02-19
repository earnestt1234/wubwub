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

class Note:
    def __init__(self, beat, pitch, length, volume):
        self.beat = beat
        self.pitch = pitch
        self.length = length
        self.volume = volume

class Chord:
    def __init__(self, beat, pitches, length, volume):
        self.beat = beat
        self.pitches = pitches
        self.length = length
        self.volume = volume

class SequencerSampler:
    def __init__(self, sample, bpm=120, timesig=4, measures=4,
                 overlap=True, basepitch='C4'):
        self.path = sample
        self.sample = pydub.AudioSegment.from_wav(sample)
        self.overlap = overlap
        self.basepitch = basepitch

        self.bpm = bpm
        self.timesig = timesig
        self.measures = measures
        self.length = timesig * measures

        self.notes = SortedDict()
        self.track = None
        self.effects = None

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

    def add_notes(self, beat, pitch=0, length=1, volume=0,
                  pitch_select='cycle', length_select='cycle',
                  volume_select='cycle'):

        if not isinstance(beat, Iterable):
            beat = [beat]

        pitch = self._convert_select_arg(pitch, pitch_select)
        length = self._convert_select_arg(length, length_select)
        volume = self._convert_select_arg(volume, volume_select)

        for i, b in enumerate(beat):
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

    def render(self):
        b = (1/self.bpm) * MINUTE
        self.track = pydub.AudioSegment.silent(duration=self.length * b)
        for beat, note in self.notes.items():
            position = (beat-1) * b
            pitch = note.pitch
            if isinstance(pitch, str):
                pitch = relative_pitch_to_int(self.basepitch, pitch)
            sound = self.sample if pitch == 0 else shift_pitch(self.sample, pitch)
            sound += note.volume
            sound = sound[:note.length * b]
            self.track = self.track.overlay(sound, position=position)
        if self.effects is not None:
            self.track = add_effects(self.track, self.effects)
        return self.track

    def play(self, rerender=True):
        play(self.render())

class Sequencer:
    def __init__(self, bpm=120, timesig=4, measures=4):
        self.bpm = bpm
        self.timesig = timesig
        self.measures = measures
        self.length = timesig * measures

        self.master = None
        self.tracks = SortedDict()
        self.sections = SortedDict()

    def add_track(self, sample, name=None, overlap=True, basepitch='C4'):
        new = SequencerSampler(sample, bpm=self.bpm, timesig=self.timesig,
                               measures=self.measures, overlap=overlap,
                               basepitch=basepitch)
        self.tracks[len(self.tracks)] = new
        return new

    def render(self):
        b = (1/self.bpm) * MINUTE
        self.master = pydub.AudioSegment.silent(duration=self.length * b)
        for instrument in self.tracks.values():
            self.master = self.master.overlay(instrument.render())
        return self.master

    def play(self, rerender=True):
        play(self.render())

class WubWubError(Exception):
    """Class for wubwub errors."""

x = Sequencer(measures=2, bpm=100)
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
