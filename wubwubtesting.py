#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

import pysndfx as sfx
import wubwub as wb
import wubwub.sounds as sounds


# load some sounds from wubwub.sounds
guitar = sounds.load('guitar')
drums1 = sounds.load('drums.esoul')
drums2 = sounds.load('drums.ukhard')
rhodes = sounds.load('keys.rhodes')
bass = sounds.load('bass.synth')
fx = sounds.load('synth.fx')

# init the sequencer
seq = wb.Sequencer(bpm=130, beats=4)

# add instruments
pluck = seq.add_sampler(guitar['electric_pluck'], name='pluck')
rhodes = seq.add_sampler(wb.shift_pitch(rhodes['A1'], 3), name='rhodes')
kick = seq.add_sampler(drums1['bdclone1'], name='kick')
snare = seq.add_sampler(drums2['snare-slam'], name='snare')
ride = seq.add_sampler(drums1['ridejazz'], name='ride')
hihat = seq.add_sampler(drums1['hhclonec'], name='hh')
bass = seq.add_sampler(wb.shift_pitch(bass['pluck'], -3), name='bass')
tiny = seq.add_sampler(fx['tiniest'], name='tiny')

# add notes
pluck.make_notes(beats=[1, 1.5, 2.5, 3.5, 4], pitches=[0, 0, -6, 1, 1])

rhodes.make_notes(beats=[1, 1.5, 2.5, 3.5, 4], pitches=[0, 0, -6, 1, 1], lengths=.25)
rhodes.effects = sfx.AudioEffectsChain().phaser()

kick.make_notes(beats=[1, 1.25, 1.5, 2.5])

snare.make_notes(beats = 3)
snare.effects = sfx.AudioEffectsChain().reverb(reverberance=10)

ride.make_notes_every(freq=2)
ride.volume = -10

hihat.make_notes_every(.5, lengths=.01)
hihat.make_notes_every(1/8, start=2.5, end=3)
hihat.make_notes(4.75)
hihat.pan = -.5

bass.make_notes(beats=[1, 1.5, 2.5, 3.5, 4], pitches=[0, 0, -6, 1, 1], lengths=.5)

tiny.make_notes_every(.5, pitches=[1, 0])
tiny.pan = +.5
tiny.effects = sfx.AudioEffectsChain().delay()


# play
looped = wb.loop(seq, 2, 1, 1)

