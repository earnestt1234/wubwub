#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:10:34 2021

@author: earnestt1234
"""

from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from collections import defaultdict
import copy
from fractions import Fraction
import itertools
from numbers import Number
import os
import warnings

import numpy as np
import pprint
import pydub
from pydub.playback import play
from sortedcontainers import SortedDict

from wubwub.audio import add_note_to_audio, add_effects, _overhang_to_milli
from wubwub.errors import WubWubError, WubWubWarning
from wubwub.notes import ArpChord, Chord, Note, arpeggiate, _notetypes_
from wubwub.resources import random_choice_generator, MINUTE

class SliceableDict:
    def __init__(self, d):
        self.d = d

    def __getitem__(self, keys):
        if isinstance(keys, Number):
            return {keys: self.d[keys]}
        elif isinstance(keys, slice):
            start, stop = (keys.start, keys.stop)
            start = 0 if start is None else start
            stop = np.inf if stop is None else stop
            return {k:v for k, v in self.d.items()
                    if start <= k < stop}
        elif isinstance(keys, Iterable):
            if getattr(keys, 'dtype', False) == bool:
                if not len(keys) == len(self.d):
                    raise IndexError(f'Length of boolean index ({len(keys)}) '
                                     f"does not match size of dict ({len(self)}).")
                return {k:v for boolean, (k, v) in
                        zip(keys, self.d.items()) if boolean}

            else:
                return {k: dict.get(self.d, k) for k in keys}
        else:
            raise IndexError('Could not interpret input as int, '
                             'slice, iterable, or boolean index.')

class Track(metaclass=ABCMeta):

    handle_new_notes = 'skip'
    setitem_copy = True

    def __init__(self, name, sample, sequencer, basepitch='C4'):
        self.basepitch = basepitch
        self.notedict = SortedDict()
        self.samplepath = None

        self.effects = None
        self.volume = 0
        self.pan = 0
        self.postprocess_steps = ['effects', 'volume', 'pan']

        self._name = None
        self._sample = None
        self._sequencer = None
        self.sequencer = sequencer
        self.name = name
        self.sample = sample

        self.plotting = {}

    def __repr__(self):
        return f'GenericTrack(name="{self.name}", sample="{self.samplepath}")'

    def __getitem__(self, beat):
        if isinstance(beat, Number):
            return self.notedict[beat]
        elif isinstance(beat, slice):
            start, stop = (beat.start, beat.stop)
            start = 0 if start is None else start
            stop = np.inf if stop is None else stop
            return [self.notedict[k] for k in self.notedict.keys() if start <= k < stop]
        elif isinstance(beat, Iterable):
            if getattr(beat, 'dtype', False) == bool:
                if not len(beat) == len(self.notedict):
                    raise IndexError(f'Length of boolean index ({len(beat)}) '
                                     f"does not match number of notes ({len(self.notedict)}).")
                return [self.notedict[k] for k, b in zip(self.notedict.keys(), beat)
                        if b]

            else:
                return [self.notedict[b] for b in beat]
        else:
            raise WubWubError('Index wubwub.Track with [beat], '
                              '[start:stop], or boolean index, '
                              f'not {type(beat)}')

    def __setitem__(self, beat, value):

        def prep(value, copy=True):
            return value.copy() if copy else value
        t = self.setitem_copy

        if isinstance(beat, Number):
            self.notedict[beat] = prep(value, t)
        elif isinstance(beat, slice):
            start, stop = (beat.start, beat.stop)
            start = 0 if start is None else start
            stop = np.inf if stop is None else stop
            for k, v in self.notedict.items():
                if k < start:
                    continue
                if k >= stop:
                    break
                self.notedict[k] = prep(value, t)
        elif isinstance(beat, Iterable):
            if getattr(beat, 'dtype', False) == bool:
                if not len(beat) == len(self.notedict):
                    raise IndexError(f'Length of boolean index ({len(beat)}) '
                                     f"does not match number of notes ({len(self.notedict)}).")
                if not type(value) in _notetypes_:
                    raise IndexError('Can only set with single note using '
                                     'boolean index.')
                for k, b in zip(self.notedict.keys(), beat):
                    if b:
                        self.notedict[k] = prep(value, t)
            else:
                if type(value) in _notetypes_:
                    value = [value] * len(beat)
                if len(beat) != len(value):
                    raise IndexError(f'Length of new values ({len(value)}) '
                                     'does not equal length of indexer '
                                     f'({len(beat)}).')
                for b, v in zip(beat, value):
                    self.notedict[b] = prep(v, t)

        else:
            raise WubWubError('Index wubwub.Track with [beat], '
                              '[start:stop], or boolean index, '
                              f'not {type(beat)}')

    def noteslicer(self):
        return SliceableDict(self.notedict)

    def ns(self):
        return SliceableDict(self.notedict)

    @property
    def sequencer(self):
        return self._sequencer

    @sequencer.setter
    def sequencer(self, sequencer):
        if sequencer == None:
            self._sequencer = None
            return

        if self._name in sequencer.tracknames():
            raise WubWubError(f'name "{self._name}" already in use by new sequencer')

        if self._sequencer is not None:
            self._sequencer.delete_track(self)
        self._sequencer = sequencer
        self._sequencer._trackmanager.add_track(self)
        if sequencer.handle_new_track_notes == 'clean':
            self.clean()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new):
        if self.sequencer and new in self.sequencer.tracknames():
            raise WubWubError(f'track name "{new}" already in use.')
        self._name = new

    @property
    def sample(self):
        return self._sample

    @sample.setter
    def sample(self, sample):
        if isinstance(sample, str):
            _, ext = os.path.splitext(sample)
            ext = ext.lower().strip('.')
            self._sample = pydub.AudioSegment.from_file(sample,
                                                        format=ext)
            self.samplepath = os.path.abspath(sample)
        elif isinstance(sample, pydub.AudioSegment):
            self._sample = sample
        else:
            raise WubWubError('sample must be a path or pydub.AudioSegment')

    def copy(self, with_notes = True):
        c = copy.deepcopy(self)
        c.sequencer = None
        if not with_notes:
            c.notedict = SortedDict()
        return c

    def add(self, beat, element, merge=False, copy=True, outsiders=None):

        if beat >= self.get_beats() + 1:
            method = self.handle_new_notes if outsiders is None else outsiders
            options = ['skip', 'add', 'warn', 'raise']
            if method not in options:
                w = ('`method` not recognized, '
                     'defaulting to "skip".',)
                warnings.warn(w, WubWubWarning)
                method = 'skip'
            if method == 'skip':
                return
            if method == 'warn':
                s = ("Adding note on beat beyond the "
                     "sequencer's length.  See `handle_new_notes` "
                     "in class docstring for `wb.Track` to toggle "
                     "this behavior.")
                warnings.warn(s, WubWubWarning)

            elif method == 'raise':
                s = ("Tried to add note on beat beyond the "
                     "sequencer's length.  See `handle_new_notes` "
                     "in class docstring for `wb.Track` to toggle "
                     "this behavior.")
                raise WubWubError(s)

        if copy:
            element = element.copy()
        existing = self.notedict.get(beat, None)
        if existing and merge:
            element = existing + element
        self.notedict[beat] = element

    def add_fromdict(self, d, offset=0, outsiders=None, merge=False, copy=True):
        for beat, element in d.items():

            self.add(beat=beat + offset, element=element, merge=merge,
                     copy=copy, outsiders=outsiders)

    def array_of_beats(self):
        return np.array(self.notedict.keys())

    def copypaste(self, start, stop, newstart, outsiders=None, merge=False,
                  copy=True):
        section = self.ns()[start:stop]
        if section:
            offset = start - 1
            at_one = {k-offset:v for k, v in section.items()}
            self.add_fromdict(at_one, offset=newstart-1)

    def _handle_beats_dict_boolarray(self, beats):
        if getattr(beats, 'dtype', False) == bool:
            beats = self[beats].keys()
        elif isinstance(beats, dict):
            beats = beats.keys()
        elif isinstance(beats, Number):
            return [beats]
        return beats

    def quantize(self, resolution=1/4):
        bts = self.get_beats()
        targets = np.empty(0)
        if isinstance(resolution, Number):
            resolution = [resolution]
        for r in resolution:
            if (1 / r) * r != 1:
                raise WubWubError('`resolution` must evenly divide 1')
            steps = int(bts * (1 / r))
            beats = np.linspace(1, bts + 1, steps, endpoint=False)
            targets = np.append(targets, beats)
        targets = np.unique(targets)
        for b, note in self.notedict.copy().items():
            diffs = np.abs(targets - b)
            argmin = np.argmin(diffs)
            closest = targets[argmin]
            if b != closest:
                del self.notedict[b]
                self.notedict[closest] = note

    def shift(self, beats, by, merge=False):
        beats = self._handle_beats_dict_boolarray(beats)
        newkeys = [k + by if k in beats else k
                   for k in self.notedict.keys()]
        oldnotes = self.notedict.values()
        self.delete_all_notes()
        for newbeat, note in zip(newkeys, oldnotes):
            self.add(newbeat, note, merge=merge, copy=False)

    def get_bpm(self):
        return self.sequencer.bpm

    def get_beats(self):
        return self.sequencer.beats

    def count_by_beat(self, res=1):
        out = defaultdict(int)
        res = 1/res
        for beat in self.array_of_beats():
            out[np.floor(beat * res) / res] += 1

        return dict(out)

    def pprint_notedict(self):
        pprint.pprint(self.notedict)

    def clean(self):
        maxi = self.get_beats()
        self.notedict = SortedDict({b:note for b, note in self.notedict.items()
                                    if b < maxi +1})

    def delete_all(self):
        self.notedict = SortedDict({})

    def delete(self, beats):
        beats = self._handle_beats_dict_boolarray(beats)
        for beat in beats:
            del self.notedict[beat]

    def delete_fromrange(self, lo, hi):
        self.notedict = SortedDict({b:note for b, note in self.notedict.items()
                                    if not lo <= b < hi})

    def unpack_notes(self):
        unpacked = []
        for b, element in self.notedict.items():
            if isinstance(element, Note):
                unpacked.append((b, element))
            elif type(element) in [Chord, ArpChord]:
                for note in element.notes:
                    unpacked.append((b, note))
        return unpacked

    @abstractmethod
    def build(self, overhang=0, overhang_type='beats'):
        pass

    def postprocess(self, build):
        for step in self.postprocess_steps:
            if step == 'effects':
                build = add_effects(build, self.effects)
            if step == 'volume':
                build += self.volume
            if step == 'pan':
                build = build.pan(self.pan)
        return build

    def play(self, start=1, end=None, overhang=0, overhang_type='beats'):
        b = (1/self.get_bpm()) * MINUTE
        start = (start-1) * b
        if end is not None:
            end = (end-1) * b
        build = self.build(overhang, overhang_type)
        play(build[start:end])

    def soundtest(self, postprocess=True):
        test = self.sample
        if postprocess:
            test = self.postprocess(test)
        play(test)

class Sampler(Track):
    def __init__(self, name, sample, sequencer, basepitch='C4', overlap=True):
        super().__init__(name, sample, sequencer, basepitch)
        self.overlap = overlap

    def __repr__(self):
        return f'Sampler(name="{self.name}", sample="{self.samplepath}")'

    def make_notes(self, beats, pitches=0, lengths=1, volumes=0,
                   pitch_select='cycle', length_select='cycle',
                   volume_select='cycle', merge=False):

        if not isinstance(beats, Iterable):
            beats = [beats]

        pitches = self._convert_select_arg(pitches, pitch_select)
        lengths = self._convert_select_arg(lengths, length_select)
        volumes = self._convert_select_arg(volumes, volume_select)

        d = {b : Note(next(pitches), next(lengths), next(volumes))
             for b in beats}

        self.add_fromdict(d, merge=merge, copy=False)

    def make_notes_every(self, freq, offset=0, pitches=0, lengths=1, volumes=0,
                         start=1, end=None, pitch_select='cycle',
                         length_select='cycle', volume_select='cycle', merge=False):

        freq = Fraction(freq).limit_denominator()

        pitches = self._convert_select_arg(pitches, pitch_select)
        lengths = self._convert_select_arg(lengths, length_select)
        volumes = self._convert_select_arg(volumes, volume_select)

        b = Fraction(start + offset).limit_denominator()
        if end is None:
            end = self.get_beats() + 1
        d = {}
        while b < end:
            pos = b.numerator / b.denominator
            d[pos] = Note(next(pitches), next(lengths), next(volumes))
            b += freq

        self.add_fromdict(d, merge=merge, copy=False)

    def make_chord(self, beat, pitches, lengths=1, volumes=0, merge=False):
        chord = self._make_chord_assemble(pitches, lengths, volumes)
        self.add(beat, chord, merge=merge, copy=False)

    def make_chord_every(self, freq, offset=0, pitches=0, lengths=1, volumes=0,
                         start=1, end=None, merge=False):

        freq = Fraction(freq).limit_denominator()

        chord = self._make_chord_assemble(pitches, lengths, volumes)
        b = Fraction(start + offset).limit_denominator()
        if end is None:
            end = self.get_beats() + 1
        d = {}
        while b < end:
            pos = b.numerator / b.denominator
            d[pos] = chord.copy()
            b += freq
        self.add_fromdict(d, merge=merge, copy=False)

    def _make_chord_assemble(self, pitches, lengths, volumes):
        if not isinstance(pitches, Iterable) or isinstance(pitches, str):
            pitches = [pitches]

        if isinstance(lengths, Number):
            lengths = [lengths] * len(pitches)

        if isinstance(volumes, Number):
            volumes = [volumes] * len(pitches)

        notes = [Note(p, l, v) for p, l, v in zip(pitches, lengths, volumes)]
        return Chord(notes)

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
        overhang = _overhang_to_milli(overhang, overhang_type, b)
        tracklength = self.get_beats() * b + overhang
        audio = pydub.AudioSegment.silent(duration=tracklength)
        sample = self.sample
        basepitch = self.basepitch
        next_position = np.inf
        for beat, value in sorted(self.notedict.items(), reverse=True):
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

        return self.postprocess(audio)

class Arpeggiator(Track):
    def __init__(self, name, sample, sequencer, basepitch='C4', freq=.5,
                 method='up'):
        super().__init__(name, sample, sequencer, basepitch)
        self.freq = freq
        self.method = method

    def __repr__(self):
        return (f'Arpeggiator(name="{self.name}", sample="{self.samplepath}", ' +
                f'freq={self.freq}, method="{self.method}")')

    def make_chord(self, beat, pitches, length=1, merge=False):
        notes = [Note(p) for p in pitches]
        chord = ArpChord(notes, length)
        self.add(beat, chord, merge=merge, copy=False)

    def make_chord_every(self, freq, offset=0, pitches=0, length=1,
                         start=1, end=None, merge=False):
        notes = [Note(p) for p in pitches]
        chord = ArpChord(notes, length)
        b = start + offset
        if end is None:
            end = self.get_beats() + 1
        d = {}
        while b < end:
            d[b] = chord.copy()
            b += freq
        self.add_fromdict(d, merge=merge, copy=False)

    def build(self, overhang=0, overhang_type='beats'):
        b = (1/self.get_bpm()) * MINUTE
        overhang = _overhang_to_milli(overhang, overhang_type, b)
        tracklength = self.get_beats() * b + overhang
        audio = pydub.AudioSegment.silent(duration=tracklength)
        sample = self.sample
        basepitch = self.basepitch
        next_beat = np.inf
        for beat, chord in sorted(self.notedict.items(), reverse=True):
            try:
                length = chord.length
            except AttributeError:
                length = max(n.length for n in chord.notes)
            if beat + length >= next_beat:
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

        return self.postprocess(audio)

class TrackManager:
    def __init__(self, sequencer):
        self._sequencer = sequencer
        self.tracks = []

    def get_track(self, track):
        if track in self.tracks:
            return track
        try:
            return next(t for t in self.tracks if t.name == track)
        except:
            raise StopIteration(f'no track with name {track}')

    def get_tracknames(self):
        return [t.name for t in self.tracks]

    def add_track(self, track):
        if track not in self.tracks:
            self.tracks.append(track)

    def delete_track(self, track):
        self.tracks.remove(self.get_track(track))