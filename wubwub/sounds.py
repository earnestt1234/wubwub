# -*- coding: utf-8 -*-
"""
Created on Fri May 14 09:49:09 2021

@author: earne
"""

import os
import shutil
import zipfile

import gdown
import pydub

__all__ = ('available', 'download', 'load', 'listall', 'refresh',
           'search',)

CURRENTDIR = os.path.dirname(os.path.abspath(__file__))
SAMPLESDIRNAME = 'SAMPLES'
SAMPLESDIR = os.path.join(CURRENTDIR, SAMPLESDIRNAME)
EXTENSIONS = {'.wav'}
DOWNLOADID = '1vc7DVckk8iK_0KrOHUrI-ZufWqyBJ194'
PREFIX = 'https://drive.google.com/uc?id='
FULLLINK = PREFIX + DOWNLOADID
VIEWLINK = f'https://drive.google.com/file/d/{DOWNLOADID}/view'

SAMPLES = []
SAMPLEFOLDERDICT = {}

def refresh():
    global SAMPLES, SAMPLEFOLDERDICT

    SAMPLES = []
    SAMPLEFOLDERDICT = {}

    for root, _, files in os.walk(SAMPLESDIR):
        for file in files:

            name, ext = os.path.splitext(file)
            if ext.lower() not in EXTENSIONS:
                continue

            pathsplit = root.split(os.sep)
            idx = pathsplit.index(SAMPLESDIRNAME)
            key = '.'.join(pathsplit[idx+1:])
            SAMPLES.append((key, name))

            if key not in SAMPLEFOLDERDICT:
                SAMPLEFOLDERDICT[key] = root

    SAMPLES = tuple(SAMPLES)

if os.path.exists(SAMPLESDIR):
    refresh()

def available():
    return tuple(SAMPLEFOLDERDICT.keys())

def download():

    yes = input(f'Download wubwub samples (~85 MB) from {VIEWLINK}? [y/n]\n')

    if yes.lower() not in ['y', 'yes']:
        return

    outpath = os.path.join(CURRENTDIR, 'SAMPLES.zip')
    gdown.download(FULLLINK, outpath)

    with zipfile.ZipFile(outpath, 'r') as zip_ref:
        zip_ref.extractall(SAMPLESDIR)

    os.remove(outpath)

    print(f'Downloaded samples to {SAMPLESDIR}.\n')

    print('Refreshing...\n')
    refresh()
    print('Done; use `wubwub.sounds.available()` to find valid keys and '
          '`wubwub.sounds.load()` to load them.\n')

def load(key):

    if not os.path.exists(SAMPLESDIR):
        raise OSError('Cannot find samples directory; please try to '
                      'download them with `wubwub.sounds.download()`.')

    try:
        folder = SAMPLEFOLDERDICT[key]
    except KeyError:
        raise KeyError(f'Cannot find sample collection "{key}"; '
                       'use `wubwub.sounds.available()` to find valid keys')

    samples = {}

    for file in os.listdir(folder):
        name, ext = os.path.splitext(file)

        if ext.lower() not in EXTENSIONS:
            continue

        fullpath = os.path.join(folder, file)

        r = 44100
        audio = (pydub.AudioSegment.from_file(fullpath, format=ext).
                 set_frame_rate(r))
        samples[name] = audio

    return samples

def REMOVE():
    yes = input(f'Remove samples folder ("{SAMPLESDIR}") all its contents? [y/n]\n')

    if yes.lower() not in ['y', 'yes']:
        return

    shutil.rmtree(SAMPLESDIR)
    print('Finished, refreshing...\n')
    refresh()
    print('Done.\n')

def listall():
    return tuple(SAMPLES)

def search(term):
    return [(key, sample) for key, sample in SAMPLES
            if (term in key) or (term in sample)]