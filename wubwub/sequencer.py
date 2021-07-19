#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music sequencer for WubWub.

@author: earnestt1234
"""
from copy import copy
import os
import time

import pydub

from wubwub.audio import add_effects, play, _overhang_to_milli
from wubwub.errors import WubWubError
from wubwub.plots import sequencerplot
from wubwub.resources import MINUTE, unique_name
from wubwub.seqstring import seqstring
from wubwub.tracks import Sampler, Arpeggiator, MultiSampler

class Sequencer:

    def __init__(self, bpm, beats):
        self.bpm = bpm
        self.beats = beats

        self.effects = None
        self.volume = 0
        self.pan = 0
        self.postprocess_steps = ['effects', 'volume', 'pan']
        self._tracks = []

    def __repr__(self):
        l = len(self.tracks())
        return f"Sequencer(bpm={self.bpm}, beats={self.beats}, tracks={l})"

    def __getitem__(self, name):
        if not isinstance(name, str):
            e = f'Can only index Sequencer with str, not {type(name)}'
            raise WubWubError(e)
        return self.get_track(name)

    def _add_track(self, track):
        if track.name in self.tracknames():
            raise WubWubError(f'Track name "{track.name}" already in use.')
        if track.sequencer != self:
            track.sequencer = self
        if track not in self._tracks:
            self._tracks.append(track)

    def copypaste_section(self, start, stop, newstart):
        for track in self.tracks():
            track.copypaste(start, stop, newstart)

    def set_beats_and_clean(self, new):
        self.beats = new
        for track in self.tracks():
            track.clean()

    def get_track(self, track):
        if isinstance(track, str):
            try:
                return next(t for t in self._tracks if t.name == track)
            except:
                raise StopIteration(f'no track with name {track}')
        elif track in self._tracks:
            return track
        else:
            raise ValueError('Requested track is not part of sequencer.')

    def tracks(self):
        return tuple(self._tracks)

    def tracknames(self):
        return [t.name for t in self._tracks]

    def add_sampler(self, sample, name=None, overlap=False, basepitch='C4'):
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = Sampler(name=name, sample=sample, overlap=overlap,
                      basepitch=basepitch, sequencer=self)
        return new

    def add_arpeggiator(self, sample, name=None, freq=0.5, method='up',
                        basepitch='C4'):
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = Arpeggiator(name=name, sample=sample, freq=freq,
                          method=method, basepitch=basepitch,
                          sequencer=self)
        return new

    def add_multisampler(self, name=None, overlap=False):
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = MultiSampler(name=name, overlap=overlap, sequencer=self)
        return new

    def add_samplers(self, samples, names=None, overlap=False, basepitch='C4'):
        if names is None:
            names = [None] * len(samples)
        for sample, name in zip(samples, names):
            self.add_sampler(sample=sample, name=name, overlap=overlap,
                             basepitch=basepitch)

    def duplicate_track(self, track, newname=None, with_notes=True):
        if newname is None:
            newname = unique_name('Track', self.tracknames())
        dup = self.get_track(track).copy(newname=newname, with_notes=with_notes)
        return dup

    def copy(self, with_notes=True):
        if with_notes:
            return copy(self)
        else:
            c = copy(self)
            for track in c.tracks():
                track.delete_all()
            return c

    def split(self, beat):
        if not isinstance(beat, int):
            raise TypeError(f'Beat for split must be int, not {type(beat)}.')

        a1, a2 = (1, beat)
        b1, b2 = (beat, self.beats+1)

        a = self.copy(with_notes=False)
        a.beats = a2 - a1
        b = self.copy(with_notes=False)
        b.beats = b2 - b1

        for selftrack, atrack, btrack in zip(self.tracks(), a.tracks(), b.tracks()):
            anotes = selftrack.ns()[a1:a2]
            atrack.add_fromdict(anotes)
            bnotes = selftrack.ns()[b1:b2]
            btrack.add_fromdict(bnotes, offset=-b.beats)

        return a, b

    def delete_track(self, track):
        t = self.get_track(track)
        t.sequencer = None
        self._tracks.remove(t)

    def build(self, overhang=0, overhang_type='beats'):
        b = (1/self.bpm) * MINUTE
        seq_oh = _overhang_to_milli(overhang, overhang_type, b)
        tracklength = self.beats * b + seq_oh
        audio = pydub.AudioSegment.silent(duration=tracklength)
        for track in self.tracks():
            audio = audio.overlay(track.build(overhang, overhang_type))
        return self.postprocess(audio)

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
        b = (1/self.bpm) * MINUTE
        start = (start-1) * b
        if end is not None:
            end = (end-1) * b
        build = self.build(overhang, overhang_type)
        play(build[start:end])

    def loop(self, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
        looped = loop(self, times=times, internal_overhang=internal_overhang,
                      end_overhang=end_overhang, overhang_type=overhang_type)
        return looped

    def loopplay(self, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
        looped = loop(self, times=times, internal_overhang=internal_overhang,
                      end_overhang=end_overhang, overhang_type=overhang_type)
        play(looped)

    def soundtest(self, selection=None, postprocess=True, gap=.5):
        if selection is None:
            selection = self.tracks()
        else:
            selection = [self.get_track(i) for i in selection]

        for track in selection:
            print(f'Playing sample(s) for "{track.name}"...')
            time.sleep(.25)
            track.soundtest(postprocess=postprocess)
            time.sleep(gap)

    def export(self, path, overhang=0, overhang_type='beats'):
        _, fmt = os.path.splitext(path)
        build = self.build(overhang, overhang_type)
        build.export(path, format=fmt)

    def show(self, printout=True, name_cutoff=None, resolution=1,
             singlenote='■', multinote='■', empty='□', wrap=32):
        s = seqstring(self,
                      name_cutoff=name_cutoff,
                      resolution=resolution,
                      singlenote=singlenote,
                      multinote=multinote,
                      empty=empty,
                      wrap=wrap)
        if printout:
            print(s)
        else:
            return s

    def plot(self, timesig=4, grid=True, ax=None, scatter_kwds=None,
             plot_kwds=None):
        sequencerplot(self,
                      timesig=timesig,
                      grid=grid,
                      ax=ax,
                      scatter_kwds=scatter_kwds,
                      plot_kwds=plot_kwds)


def stitch(sequencers, internal_overhang=0, end_overhang=0, overhang_type='beats'):
    total_length = 0
    current = 0
    sectionstarts = []
    for seq in sequencers:
        b = (1/seq.bpm) * MINUTE
        seq_length = b * seq.beats
        total_length += seq_length
        sectionstarts.append(current)
        current += seq_length
    total_length += _overhang_to_milli(end_overhang, overhang_type, b)

    stitched = pydub.AudioSegment.silent(duration=total_length)
    for start, seq in zip(sectionstarts, sequencers):
        build = seq.build(internal_overhang, overhang_type)
        stitched = stitched.overlay(build, start)

    return stitched

def _matchesforjoin(oldtracks, newtrack, on='name'):
    ons = ['name', 'sample', 'sample+type']
    if on not in ons:
        raise WubWubError(f'`on` must be selected from {ons}')

    if on == 'name':
        return [track for track in oldtracks if track.name == newtrack.name]
    if on == 'sample':
        return [track for track in oldtracks if track.sample == newtrack.sample]
    if on == 'sample+type':
        return [track for track in oldtracks if track.sample == newtrack.sample
                and type(track) == type(newtrack)]
    return []

def join(sequencers, on='name'):
    beats = sum(seq.beats for seq in sequencers)
    out = Sequencer(bpm=sequencers[0].bpm, beats=beats)
    offset = 0
    for i, seq in enumerate(sequencers):
        oldtracks = out.tracks()
        available = list(oldtracks)

        for track in seq.tracks():
            match = None
            matches = _matchesforjoin(available, track, on=on)
            if matches:
                match = matches[0]
                available.remove(match)

            if match:
                match.add_fromdict(track.notedict, offset=offset)

            else:
                new = track.copy(with_notes=False)
                new.sequencer = out
                new.add_fromdict(track.notedict, offset=offset)


        offset = seq.beats
    return out




def loop(sequencer, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):

    return stitch([sequencer] * times,
                  internal_overhang,
                  end_overhang,
                  overhang_type)


