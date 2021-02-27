#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb

seq = wb.Sequencer(bpm=100, beats=16)

synth = seq.add_sampler('samples/trumpet.WAV', name='Synth')
synth.make_notes([1, 3, 5, 7], pitches=[0, 8, 3, 7],)

kick = seq.add_sampler('samples/808/kick (5).wav')
kick.make_notes_every(freq=1)
kick[1.25] = wb.Note()

snare = seq.add_sampler('samples/808/snare (3).wav')
snare.make_notes_every(2, offset=1)

hihat = seq.add_sampler('samples/808/hi hat (1).wav')
hihat.make_notes_every(1/2)

wb.sequencer_plot(seq)
# seq.play()
