#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb

seq = wb.Sequencer(bpm=100, beats=8)

synth = seq.add_sampler('samples/trumpet.WAV', name='synth')
synth.make_notes([1, 3, 5, 7], pitches=[0, 8, 3, 7],)
synth.make_notes([1, 3, 5, 7], pitches=[3, 12, 7, 10], merge=True)
synth.make_notes([1, 3, 5, 7], pitches=[7, 3, 10, 14], merge=True)
synth.effects = AudioEffectsChain().reverb()

kick = seq.add_sampler('samples/808/kick (5).wav', name='kick')
kick.make_notes_every(freq=1)
kick[1.25] = wb.Note()

snare = seq.add_sampler('samples/808/snare (3).wav', name='snare')
snare.make_notes_every(2, offset=1)

hihat = seq.add_sampler('samples/808/hi hat (1).wav', name='hi-hat')
hihat.make_notes_every(1/2)

hihat.plotting['color'] = 'slateblue'

# wb.sequencerplot(seq)
# wb.trackplot(synth, 'pitch')
# seq.play()

wb.pianoroll(synth, grid=True)
# wb.trackplot(synth, yaxis='pitch')


#%%

test = wb.Sequencer(bpm=100, beats=4)
a = test.add_sampler('samples/trumpet.WAV')
b = test.add_sampler('samples/trumpet.WAV')