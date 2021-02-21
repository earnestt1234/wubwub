#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb


x = wb.Sequencer(bpm=100, beats=8)
hihat = x.add_sampler('samples/808/hi hat (1).wav')
snare = x.add_sampler('samples/808/snare (1).wav')
kick = x.add_sampler('samples/808/kick (11).wav')
synth = x.add_sampler('samples/trumpet.wav')
hihat.add_notes_every(1/4)
snare.add_notes_every(2, 1)
kick.add_notes_every(1)
synth.add_notes_every(.5, pitch=0, length=.25)
synth.add_notes_every(.5, pitch=3, length=.25, merge=True)
synth.add_notes_every(.5, pitch=7, length=.25, merge=True)

fx = AudioEffectsChain().reverb(wet_gain=10)
synth.effects=fx

synth.pprint_notes()

x.play()