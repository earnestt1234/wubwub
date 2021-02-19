#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:13:53 2021

@author: earnestt1234
"""

class Note:
    def __init__(self, beat, pitch, length, volume):
        self.beat = beat
        self.pitch = pitch
        self.length = length
        self.volume = volume

    def __repr__(self):
        attribs = ', '.join([str(k)+'='+str(v) for k, v in vars(self).items()])
        return f'Note({attribs})'

class Chord:
    def __init__(self, beat, pitches, length, volume):
        self.beat = beat
        self.pitches = pitches
        self.length = length
        self.volume = volume

    def __repr__(self):
        attribs = ', '.join([str(k)+'='+str(v) for k, v in vars(self).items()])
        return f'Chord({attribs})'