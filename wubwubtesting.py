#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb

x = wb.Sequencer(bpm=100, beats=8)
hihat = x.new_track('808/hi hat (1).wav')
snare = x.new_track('808/snare (1).wav')
kick = x.new_track('808/kick (11).wav')
synth = x.new_track('trumpet.wav')
hihat.new_notes_every(1/4)
snare.new_notes_every(2, 1)
kick.new_notes_every(1)
synth.new_notes([1, 3, 5, 7], pitch=[0, 8, 3, 7], length=2)

fx = AudioEffectsChain().reverb()
synth.effects=fx

# x.play()


#%%

# imports
import matplotlib.pyplot as plt
import numpy as np
import wave, sys

# shows the sound waves
def visualize(signal, f_rate):
    signal = np.abs(np.array(signal))
    x = np.arange(0, len(signal), 500)
    y = signal[x]
    plt.fill_between(x, -y, y)

visualize(x.build().get_array_of_samples(), 44100)

#%%

import scipy.io.wavfile

sr, y = scipy.io.wavfile.read('/Users/earnestt1234/Desktop/test.wav')
plt.plot(y)