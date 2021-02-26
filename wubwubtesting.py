#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb


x = wb.Sequencer(bpm=300, beats=7 * 4)
hihat = x.add_sampler('samples/808/hi hat (1).wav')
snare = x.add_sampler('samples/808/snare (1).wav')
kick = x.add_sampler('samples/808/kick (11).wav')
synth = x.add_arpeggiator('samples/trumpet.wav', freq=1/4)
hihat.make_notes(wb.repeated_measures([1, 4, 6], measurelen=7, measures=4))
kick.make_notes(wb.repeated_measures([1, 1.5], measurelen=7, measures=4))
snare.make_notes(wb.repeated_measures([4, 7], measurelen=7, measures=4))

x.play()