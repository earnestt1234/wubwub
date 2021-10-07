#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:17:19 2021

@author: earnestt1234
"""

import array

import numpy as np
from pydub.playback import play as _play

from wubwub.errors import WubWubError
from wubwub.pitch import relative_pitch_to_int, shift_pitch

__pdoc__ = {'add_note_to_audio': False,
            'add_effects': False}

def add_note_to_audio(note, audio, sample, position, duration, basepitch=None,
                      fade=10, shift=True):
    if shift:
        pitch = note.pitch
        if pitch is None:
            return audio
        if isinstance(pitch, str) and pitch != 0:
            pitch = relative_pitch_to_int(basepitch, pitch)
        sample = shift_pitch(sample, pitch)
    sound = sample
    sound += note.volume
    sound = sound[:duration]
    sound = sound.fade_out(fade)
    audio = audio.overlay(sound, position=position)
    return audio

def add_effects(sound, fx):
    if fx is None:
        return sound
    samples = np.array(sound.get_array_of_samples())
    samples = fx(samples)
    samples = array.array(sound.array_type, samples)
    effected = sound._spawn(samples)
    return effected

def _overhang_to_milli(overhang, overhang_type, b=600):
    if overhang_type == 'beats':
        overhang = b * overhang
    elif overhang_type in ['s', 'seconds']:
        overhang = overhang * 1000
    else:
        raise WubWubError('overhang must be "beats" or "seconds"')
    return overhang

def play(audiosegment, convert=True):
    if audiosegment.sample_width != 2:
        if convert:
            audiosegment = audiosegment.set_sample_width(2).set_frame_rate(44100)
        else:
            raise WubWubError('wubwub can only play 16-bit sounds, '
                              'either use the `convert` parameter '
                              'or otherwise convert the sound to be 16-bit.')
    _play(audiosegment)