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
import pprint
import warnings

import numpy as np
import pydub
from sortedcontainers import SortedDict

from wubwub.audio import add_note_to_audio, add_effects, play, _overhang_to_milli
from wubwub.errors import WubWubError, WubWubWarning
from wubwub.notes import ArpChord, Chord, Note, arpeggiate, _notetypes_
from wubwub.plots import trackplot, pianoroll
from wubwub.resources import random_choice_generator, MINUTE, SECOND

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

    handle_outside_notes = 'skip'

    def __init__(self, name, sequencer,):
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

        self.plotting = {}

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
        if isinstance(beat, Number):
            self.notedict[beat] = value
        elif isinstance(beat, slice):
            start, stop, step = (beat.start, beat.stop, beat.step)
            if step is None:
                # replace all notes in the range
                start = 0 if start is None else start
                stop = np.inf if stop is None else stop
                for k, v in self.notedict.items():
                    if k < start:
                        continue
                    if k >= stop:
                        break
                    self.notedict[k] = value
            else:
                # fill notes from start to stop every step
                start = 1 if start is None else start
                stop = self.get_beats() + 1 if stop is None else stop
                while start < stop:
                    self.notedict[start] = value
                    start += step
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
                        self.notedict[k] = value
            else:
                if type(value) in _notetypes_:
                    value = [value] * len(beat)
                if len(beat) != len(value):
                    raise IndexError(f'Length of new values ({len(value)}) '
                                     'does not equal length of indexer '
                                     f'({len(beat)}).')
                for b, v in zip(beat, value):
                    self.notedict[b] = v

        else:
            raise WubWubError('Index wubwub.Track with [beat], '
                              '[start:stop], or boolean index, '
                              f'not {type(beat)}')

    @property
    def slice(self):
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
        self._sequencer._add_track(self)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new):
        if self.sequencer and new in self.sequencer.tracknames():
            raise WubWubError(f'track name "{new}" already in use.')
        self._name = new

    def add(self, beat, element, merge=False, outsiders=None):

        if beat >= self.get_beats() + 1:
            method = self.handle_outside_notes if outsiders is None else outsiders
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
                     "sequencer's length.  See `handle_outside_notes` "
                     "in class docstring for `wb.Track` to toggle "
                     "this behavior.")
                warnings.warn(s, WubWubWarning)

            elif method == 'raise':
                s = ("Tried to add note on beat beyond the "
                     "sequencer's length.  See `handle_outside_notes` "
                     "in class docstring for `wb.Track` to toggle "
                     "this behavior.")
                raise WubWubError(s)
        existing = self.notedict.get(beat, None)
        if existing and merge:
            element = existing + element
        self.notedict[beat] = element

    def add_fromdict(self, d, offset=0, outsiders=None, merge=False):
        for beat, element in d.items():

            self.add(beat=beat + offset, element=element, merge=merge,
                     outsiders=outsiders)

    def array_of_beats(self):
        return np.array(self.notedict.keys())

    def copy(self, newname=None, newseq=False, with_notes=True,):
        if newname is None:
            newname = self.name
        if newseq is False:
            newseq = self.sequencer
        new = copy.copy(self)
        for k, v in vars(new).items():
            if k == 'notedict':
                setattr(new, k, v.copy())
            elif k == '_name':
                setattr(new, k, newname)
            elif k == '_sequencer':
                setattr(new, k, None)
            else:
                setattr(new, k, copy.deepcopy(v))
        new.sequencer = newseq
        if not with_notes:
            new.delete_all()
        return new

    def copypaste(self, start, stop, newstart, outsiders=None, merge=False,):
        section = self.slice[start:stop]
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

    def quantize(self, resolution=1/4, merge=False):
        bts = self.get_beats()
        targets = np.empty(0)
        if isinstance(resolution, Number):
            resolution = [resolution]
        for r in resolution:
            if ((1 / r) % 1) != 0:
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
                self.add(closest, note, merge=merge)

    def shift(self, beats, by, merge=False):
        beats = self._handle_beats_dict_boolarray(beats)
        newkeys = [k + by if k in beats else k
                   for k in self.notedict.keys()]
        oldnotes = self.notedict.values()
        self.delete_all_notes()
        for newbeat, note in zip(newkeys, oldnotes):
            self.add(newbeat, note, merge=merge)

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
                                    if 1 <= b < maxi +1})

    def delete_all(self):
        self.notedict = SortedDict({})

    def delete(self, beats):
        beats = self._handle_beats_dict_boolarray(beats)
        for beat in beats:
            del self.notedict[beat]

    def delete_fromrange(self, lo, hi):
        self.notedict = SortedDict({b:note for b, note in self.notedict.items()
                                    if not lo <= b < hi})

    def unpack_notes(self, start=0, stop=np.inf,):
        unpacked = []
        for b, element in self.notedict.items():
            if not start <= b < stop:
                continue
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

    @abstractmethod
    def soundtest(self, duration=None, postprocess=True,):
        pass

    def plot(self, yaxis='semitones', timesig=4, grid=True, ax=None,
             plot_kwds=None, scatter_kwds=None):
        return trackplot(track=self,
                         yaxis=yaxis,
                         timesig=timesig,
                         grid=grid,
                         ax=ax,
                         plot_kwds=plot_kwds,
                         scatter_kwds=scatter_kwds)

    def pianoroll(self, timesig=4, grid=True,):
        return pianoroll(track=self, timesig=timesig, grid=grid)

class SamplerLikeTrack(Track):
    def __init__(self, name, sequencer, **kwargs):
        super().__init__(name=name, sequencer=sequencer)

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

        self.add_fromdict(d, merge=merge)

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

        self.add_fromdict(d, merge=merge)

    def make_chord(self, beat, pitches, lengths=1, volumes=0, merge=False):
        chord = self._make_chord_assemble(pitches, lengths, volumes)
        self.add(beat, chord, merge=merge)

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
            d[pos] = chord
            b += freq
        self.add_fromdict(d, merge=merge)

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

class SingleSampleTrack(Track):
    def __init__(self, name, sample, sequencer, **kwargs):
        super().__init__(name=name, sequencer=sequencer, **kwargs)
        self._sample = None
        self.sample = sample

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

class MultiSampleTrack(Track):
    def __init__(self, name, sequencer, **kwargs):
        super().__init__(name=name, sequencer=sequencer, **kwargs)
        self.samples = {}

class Sampler(SingleSampleTrack, SamplerLikeTrack):
    def __init__(self, name, sample, sequencer, basepitch='C4', overlap=True):
        super().__init__(name=name, sample=sample, sequencer=sequencer,
                         basepitch=basepitch, overlap=overlap)
        self.overlap = overlap
        self.basepitch = basepitch

    def __repr__(self):
        return f'Sampler(name="{self.name}")'

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

    def soundtest(self, duration=None, postprocess=True,):
        test = self.sample
        if postprocess:
            test = self.postprocess(test)
        if duration is None:
            duration = len(test)
        else:
            duration = duration * SECOND
        play(test[:duration])

class MultiSampler(MultiSampleTrack, SamplerLikeTrack):
    def __init__(self, name, sequencer, overlap=True):
        super().__init__(name=name, sequencer=sequencer)
        self.overlap = overlap
        self.default_sample = pydub.AudioSegment.empty()

    def __repr__(self):
        return f'MultiSampler(name="{self.name}")'

    def build(self, overhang=0, overhang_type='beats'):
        b = (1/self.get_bpm()) * MINUTE
        overhang = _overhang_to_milli(overhang, overhang_type, b)
        tracklength = self.get_beats() * b + overhang
        audio = pydub.AudioSegment.silent(duration=tracklength)
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
                                          sample=self.get_sample(note.pitch),
                                          position=position,
                                          duration=duration,
                                          shift=False)
            elif isinstance(value, Chord):
                chord = value
                for note in chord.notes:
                    duration = note.length * b
                    if (position + duration) > next_position and not self.overlap:
                        duration = next_position - position
                    audio = add_note_to_audio(note=note,
                                              audio=audio,
                                              sample=self.get_sample(note.pitch),
                                              position=position,
                                              duration=duration,
                                              shift=False)
                next_position = position

        return self.postprocess(audio)

    def soundtest(self, duration=None, postprocess=True,):
        for k, v in self.samples.items():
            test = v
            if postprocess:
                test = self.postprocess(test)
            if duration is None:
                duration = len(test)
            else:
                duration = duration * SECOND
            play(test[:duration])

    def add_sample(self, key, sample):
        if isinstance(sample, str):
            _, ext = os.path.splitext(sample)
            ext = ext.lower().strip('.')
            self.samples[key] = pydub.AudioSegment.from_file(sample,
                                                             format=ext)
        elif isinstance(sample, pydub.AudioSegment):
            self.samples[key] = sample
        else:
            raise WubWubError('sample must be a path or pydub.AudioSegment')

    def get_sample(self, key):
        return self.samples.get(key, self.default_sample)

class Arpeggiator(SingleSampleTrack):
    def __init__(self, name, sample, sequencer, basepitch='C4', freq=.5,
                 method='up'):
        super().__init__(name=name, sample=sample, sequencer=sequencer,)
        self.freq = freq
        self.method = method
        self.basepitch = basepitch

    def __repr__(self):
        return (f'Arpeggiator(name="{self.name}", '
                f'freq={self.freq}, method="{self.method}")')

    def make_chord(self, beat, pitches, length=1, merge=False):
        notes = [Note(p) for p in pitches]
        chord = ArpChord(notes, length)
        self.add(beat, chord, merge=merge,)

    def make_chord_every(self, freq, offset=0, pitches=0, length=1,
                         start=1, end=None, merge=False):
        notes = [Note(p) for p in pitches]
        chord = ArpChord(notes, length)
        b = start + offset
        if end is None:
            end = self.get_beats() + 1
        d = {}
        while b < end:
            d[b] = chord
            b += freq
        self.add_fromdict(d, merge=merge)

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

    def soundtest(self, duration=None, postprocess=True,):
        test = self.sample
        if postprocess:
            test = self.postprocess(test)
        if duration is None:
            duration = len(test)
        else:
            duration = duration * SECOND
        play(test[:duration])

    def unpack_notes(self, start=0, stop=np.inf,):
        unpacked = []
        for b, element in self.notedict.items():
            if not start <= b < stop:
                continue
            if isinstance(element, Note):
                unpacked.append((b, element))
            elif type(element) in [Chord, ArpChord]:
                arpeggiated = arpeggiate(element, beat=b,
                                         freq=self.freq, method=self.method)
                for k, v in arpeggiated.items():
                    unpacked.append((k, v))

        return unpacked