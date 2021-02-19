#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 19 14:11:33 2021

@author: earnestt1234
"""

import array

import numpy as np
from pydub import AudioSegment
from pydub.playback import play

a = x.build()

res = 100 # ms
low = 50
high = 20000

def add_effects(sound, fx):
    samples = np.array(sound.get_array_of_samples())
    samples = fx(samples)
    samples = array.array(sound.array_type, samples)
    effected = sound._spawn(samples)
    return effected



if len(a) % res == 0:
    framelen = len(a) // res
else:
    framelen = (len(a) // res) + 1
freqs = np.linspace(low, high, framelen)

new = AudioSegment.silent(duration=len(a))
for i in range(framelen):
    audioframe = a[i*res:i*res+res]
    fx = AudioEffectsChain().lowpass(frequency=freqs[i])
    audioframe = add_effects(audioframe, fx)
    audioframe = audioframe.fade_in(10)
    new = new.overlay(audioframe, position=i*res)

play(new)
