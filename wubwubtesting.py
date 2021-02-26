#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

from pysndfx import AudioEffectsChain
import wubwub as wb

seq = wb.Sequencer(bpm=100, beats=8)

synth = seq.add_sampler('samples/trumpet.WAV', name='Synth')
synth.make_notes([2.5, 4.5, 6.5, 8.5], pitches=[0, 7, 8, 5, 0], lengths=1)
synth.make_notes([2.5, 4.5, 6.5, 8.5], pitches=[7, 14, 15, 12, 7], lengths=1,
                 merge=True)

synth.effects = AudioEffectsChain().lowpass(1200).reverb().delay(delays=[600])

kick = seq.add_sampler('samples/808/kick (5).WAV')
kick.make_notes_every(freq=1)

