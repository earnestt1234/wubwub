#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb  9 10:27:15 2021

@author: earnestt1234
"""

import pysndfx as sfx
import wubwub as wb
import wubwub.sounds as sounds

# init the sequencer
seq = wb.Sequencer(bpm=130, beats=4)
m = seq.add_multisampler(name='tom',)