#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module provides some functions for manipulating pydub AudioSegments.
"""

import array

import numpy as np
from pydub.playback import play as _play

from wubwub.errors import WubWubError
from wubwub.pitch import relative_pitch_to_int, shift_pitch

__pdoc__ = {'add_note_to_audio': False,
            'add_effects': False}

def add_note_to_audio(note, audio, sample, position, duration, basepitch=None,
                      fade=10, shift=True):
    '''
    A function for adding a `wubwub.notes.Note` onto an pydub AudioSegment.

    Parameters
    ----------
    note : wubwub.notes.Note
        Note to add.
    audio : pydub.AudioSegment
        Audio to be added onto.
    sample : pydub.AudioSegment
        New sample to be added.
    position : int or float
        Position in the audio to add the new sample.
    duration : int
        Duration of the sample to add.
    basepitch : str or number, optional
        Basepitch for the sample; used for shifting the pitch.
        The default is None.
    fade : int, optional
        Fade (in milliseconds) for the end of the sample. The default is 10.
    shift : bool, optional
        Whether to shift the pitch of the sample or not. The default is True.

    Returns
    -------
    audio : pydub.AudioSegment
        Audio with the sample added.

    '''
    if shift:
        pitch = note.pitch
        if pitch is None:
            return audio
        if isinstance(pitch, str) and pitch != 0:
            pitch = relative_pitch_to_int(basepitch, pitch)
        sample = shift_pitch(sample, pitch)
    sound = sample
    sound += note.volume
    sound = sound[:duration]
    sound = sound.fade_out(fade)
    audio = audio.overlay(sound, position=position)
    return audio

def add_effects(sound, fx):
    '''Add a pysndfx AudioEffectsChain to a pydub AudioSegment.'''
    if fx is None:
        return sound
    samples = np.array(sound.get_array_of_samples())
    samples = fx(samples)
    samples = array.array(sound.array_type, samples)
    effected = sound._spawn(samples)
    return effected

def _overhang_to_milli(overhang, overhang_type, b=600):
    '''Return an ovehang in seconds or beats into milliseconds.'''
    if overhang_type == 'beats':
        overhang = b * overhang
    elif overhang_type in ['s', 'seconds']:
        overhang = overhang * 1000
    else:
        raise WubWubError('overhang must be "beats" or "seconds"')
    return overhang

def play(audiosegment, convert=True):
    '''Playback a pydub AudioSegment.  Essentially calls `pydub.play`.

    Note that wubwub only plays sounds if they are 16-bit and have a 44100Hz
    sample rate.  If `convert` is `True` (default), sounds that do not meet
    this criteria will be converted.  If not, the sound will not be played.
    This is due to the author's personal experience with some buggy sound
    playback (see here: https://stackoverflow.com/q/68355805/13386979).

    To get around the limitation imposed here, you can instead use
    `pydub.play` on any AudioSegments produced in wubwub.'''
    if audiosegment.sample_width != 2:
        if convert:
            audiosegment = audiosegment.set_sample_width(2).set_frame_rate(44100)
        else:
            raise WubWubError('wubwub can only play 16-bit sounds, '
                              'either use the `convert` parameter '
                              'or otherwise convert the sound to be 16-bit.')
    _play(audiosegment)