#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb


x = wb.Sequencer(bpm=60, beats=4)
hihat = x.add_sampler('samples/808/hi hat (1).wav')
snare = x.add_sampler('samples/808/snare (1).wav')
kick = x.add_sampler('samples/808/kick (11).wav')
synth = x.add_arpeggiator('samples/trumpet.wav', freq=1/4)
hihat.make_notes_every(1/4)
snare.make_notes_every(2, 1)
kick.make_notes_every(1)
synth.make_chord(1, pitches=[0,3,7], length=4)

fx = AudioEffectsChain().reverb()
synth.effects=fx

y = x.copy()
synth2 = y['Track4']

# x.play()

a = wb.stitch([x, y])
# wb.play(a)

# d = wb.SliceableDict({1:'a', 2:'b'})