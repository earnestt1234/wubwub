# -*- coding: utf-8 -*-
"""
Created on Fri May 14 09:49:09 2021

@author: earne
"""

import os
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
    outpath = os.path.join(CURRENTDIR, 'SAMPLES.zip')
    gdown.download(FULLLINK, outpath)

    with zipfile.ZipFile(outpath, 'r') as zip_ref:
        zip_ref.extractall(CURRENTDIR)

    os.remove(outpath)

    refresh()

def load(key):

    if not os.path.exists(SAMPLESDIR):
        raise OSError('Cannot find samples directory; please try to '
                      'download them with `wubwubsounds.download()`.')

    try:
        folder = SAMPLEFOLDERDICT[key]
    except KeyError:
        raise KeyError(f'Cannot find sample collection "{key}"; '
                       'use `wubwubsounds.available()` to find valid keys')

    samples = {}

    for file in os.listdir(folder):
        name, ext = os.path.splitext(file)

        if ext.lower() not in EXTENSIONS:
            continue

        fullpath = os.path.join(folder, file)

        samples[name] = pydub.AudioSegment.from_file(fullpath, format=ext)

    return samples

def listall():
    return tuple(SAMPLES)

def search(term):
    return [(key, sample) for key, sample in SAMPLES
            if (term in key) or (term in sample)]