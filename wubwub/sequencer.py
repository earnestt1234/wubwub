#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music sequencer for WubWub.

@author: earnestt1234
"""
from copy import deepcopy
import time

import pydub
from pydub.playback import play

from wubwub.audio import add_effects, _overhang_to_milli
from wubwub.errors import WubWubError
from wubwub.resources import MINUTE, unique_name
from wubwub.tracks import TrackManager, Sampler, Arpeggiator

class Sequencer:

    handle_new_track_notes = 'clean'

    def __init__(self, bpm, beats):
        self.bpm = bpm
        self.beats = beats
        self._trackmanager = TrackManager(self)

        self.effects = None
        self.volume = 0
        self.pan = 0
        self.postprocess_steps = ['effects', 'volume', 'pan']

        self.volume = 0
        self.pan = 0
        self.effects = None

    def __repr__(self):
        l = len(self.tracks())
        return f"Sequencer(bpm={self.bpm}, beats={self.beats}, tracks={l})"

    def __getitem__(self, name):
        if not isinstance(name, str):
            e = f'Can only index Sequencer with str, not {type(name)}'
            raise WubWubError(e)
        return self._trackmanager.get_track(name)

    def copypaste_section(self, start, stop, newstart):
        for track in self.tracks():
            track.copypaste(start, stop, newstart)

    def set_beats_and_clean(self, new):
        self.beats = new
        for track in self.tracks():
            track.clean()

    def get_track(self, track):
        return self._trackmanager.get_track(track)

    def tracks(self):
        return tuple(self._trackmanager.tracks)

    def tracknames(self):
        return self._trackmanager.get_tracknames()

    def add_sampler(self, sample, name=None, overlap=True, basepitch='C4'):
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

    def duplicate_track(self, track, newname=None):
        if newname is None:
            newname = unique_name('Track', self.tracknames())
        copy = deepcopy(self.get_track(track))
        copy.name = newname
        self._trackmanager.add_track(copy)
        return copy

    def copy(self):
        return deepcopy(self)

    def delete_track(self, track):
        self._trackmanager.delete_track(track)

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
        play(looped)


    def soundtest(self, selection=None, postprocess=True, gap=.5):
        if selection is None:
            selection = self.tracks()
        else:
            selection = [self._trackmanager.get_track(i) for i in selection]

        for track in selection:
            print(f'Playing sample(s) for "{track.name}"...')
            time.sleep(.25)
            track.soundtest(postprocess=postprocess)
            time.sleep(gap)

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

def loop(sequencer, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
    return stitch([sequencer] * times, internal_overhang, end_overhang,
                  overhang_type)


