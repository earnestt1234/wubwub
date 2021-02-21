#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music sequencer for WubWub.

@author: earnestt1234
"""
import time

import pydub
from pydub.playback import play

from wubwub.audio import add_effects
from wubwub.errors import WubWubError
from wubwub.resources import MINUTE, SECOND, unique_name
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

    def set_beats_and_clean(self, new):
        self.beats = new
        for track in self.tracks():
            track.clean()

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

    def delete_track(self, track):
        self._trackmanager.delete_track(track)

    def build(self, overhang=0, overhang_type='beats'):
        b = (1/self.bpm) * MINUTE
        if overhang_type == 'beats':
            seq_oh = b * overhang
        elif overhang_type in ['s', 'seconds']:
            seq_oh = overhang * 1000
        else:
            raise WubWubError('overhang must be "beats" or "seconds"')
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

