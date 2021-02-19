#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb


x = wb.Sequencer(bpm=100, beats=8)
hihat = x.new_sampler('samples/808/hi hat (1).wav')
snare = x.new_sampler('samples/808/snare (1).wav')
kick = x.new_sampler('samples/808/kick (11).wav')
synth = x.new_arpeggiator('samples/trumpet.wav', freq=1/6)
hihat.new_notes_every(1/3)
snare.new_notes_every(2, 1)
kick.new_notes_every(1)
synth.new_arpeggio(1, pitches=[0,3,7,10,12,14], length=10)

fx = AudioEffectsChain().reverb()
synth.effects=fx

x.play(overhang=4)
