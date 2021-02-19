#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Music sequencer for WubWub.

@author: earnestt1234
"""

import pydub
from pydub.playback import play

from wubwub.audio import add_effects
from wubwub.errors import WubWubError
from wubwub.resources import MINUTE
from wubwub.tracks import TrackManager

class Sequencer:
    def __init__(self, bpm, beats):
        self.bpm = bpm
        self.beats = beats
        self.__trackmanager = TrackManager(self)

        self.effects = None

    def __repr__(self):
        l = len(self.tracks())
        return f"Sequencer(bpm={self.bpm}, beats={self.beats}, tracks={l})"

    def __getitem__(self, name):
        if not isinstance(name, str):
            e = f'Can only index Sequencer with str, not {type(name)}'
            raise WubWubError(e)
        return self.__trackmanager.get_track(name)

    def tracks(self):
        return tuple(self.__trackmanager.tracks)

    def tracknames(self):
        return self.__trackmanager.get_tracknames()

    def new_track(self, sample, name=None, overlap=True, basepitch='C4'):
        if name is None:
            names = self.tracknames()
            base = "Track"
            c = 1
            while name in names or name is None:
                name = base + str(c)
                c += 1
        return self.__trackmanager.new_track(name=name, sample=sample,
                                             overlap=overlap, basepitch=basepitch)

    def delete_track(self, track):
        self.__trackmanager.delete_track(track)

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
        if self.effects:
            audio = add_effects(audio, self.effects)
        return audio

    def play(self, overhang=0, overhang_type='beats'):
        play(self.build(overhang, overhang_type))


