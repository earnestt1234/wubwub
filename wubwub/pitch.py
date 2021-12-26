#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functions and resources for dealing with pitch in wubwub.
"""

import re

from wubwub.errors import WubWubError

NOTES = ['C' , 'C#', 'Db', 'D' , 'D#', 'Eb', 'E' , 'F', 'F#',
         'Gb', 'G' , 'G#', 'Ab', 'A' , 'A#', 'Bb', 'B',]
DIFF =  [0   , 1   , 1   , 2   , 3   , 3   , 4   , 5   , 6   ,
         6   , 7   , 8   , 8   , 9   , 10  , 10  , 11  ]
NOTES_JOIN = '|'.join(NOTES)

named_chords = (
    {''     : (0, 4, 7),
     'M'    : (0, 4, 7),
     'major': (0, 4, 7),
     'maj7' : (0, 4, 7, 11),
     'M7'   : (0, 4, 7, 11),
     'm'    : (0, 3, 7),
     'minor': (0, 3, 7),
     'min7' : (0, 3, 7, 10),
     'm7'   : (0, 3, 7, 10),
     '+'    : (0, 4, 8),
     'aug'  : (0, 4, 8),
     'dim'  : (0, 3, 6),
     '7'    : (0, 4, 7, 10)})
"""Dictionary of pitches (relative to the root) for severval classes of chord."""

chordnames_re = '|'.join(named_chords.keys())

def valid_chord_str(s):
    '''Returns True if `s` is a valid chord string.'''
    pattern = f"^({NOTES_JOIN})({chordnames_re})$"
    return bool(re.match(pattern, s))

def valid_pitch_str(s):
    '''Returns True is `s` is a valid scientific pitch string.'''
    pattern = f"^({NOTES_JOIN})[0-9]$"
    return bool(re.match(pattern, s))

def pitch_from_semitones(pitch, semitones):
    '''
    Return a new pitch string, based on a difference in semitones from an
    initial pitch string.

    Parameters
    ----------
    pitch : str
        Scientific pitch string.
    semitones : int
        Difference in semitones from `pitch`.

    Returns
    -------
    str
        New scientific pitch string

    '''
    oldname, oldoct = splitoctave(pitch)
    idx_old = NOTES.index(oldname)
    old_diff = DIFF[idx_old]
    octave_change = (old_diff + semitones) // 12
    new_diff = semitones + old_diff
    new_diff = (new_diff % 12) if (new_diff >= 0) else ((12 + (new_diff % -12)) % 12)
    newpitch = NOTES[DIFF.index(new_diff)]
    return newpitch + str(oldoct + octave_change)

def relative_pitch_to_int(a, b):
    pitch_a, octave_a = splitoctave(a)
    pitch_b, octave_b = splitoctave(b)
    octave_diff = octave_b - octave_a
    pitch_diff = DIFF[NOTES.index(pitch_b)] - DIFF[NOTES.index(pitch_a)]
    return pitch_diff + (12 * octave_diff)

def splitoctave(pitch_str, octave_type=int):
    if not valid_pitch_str(pitch_str):
        raise WubWubError(f'"{pitch_str}" is not a valid pitch string')
    return pitch_str[:-1], octave_type(pitch_str[-1])

def splitchordname(chord_str):
    if not valid_chord_str(chord_str):
        raise WubWubError(f'"{chord_str}" is not a valid chord string')
    if chord_str[1] in ['#, b']:
        return chord_str[:2], chord_str[2:]
    else:
        return chord_str[:1], chord_str[1:]

def shift_pitch(sound, semitones):
    octaves = (semitones/12)
    new_sample_rate = int(sound.frame_rate * (2.0 ** octaves))
    new_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_sample_rate})
    new_sound = new_sound.set_frame_rate(44100)
    return new_sound