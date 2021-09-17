#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create string diagrams showing the content of a Sequencer.

The diagram is essentially a boolean grid, where the rows are Tracks and the
columns are beats. Cells are filled when the given Track contains a Note/Chord
on the given beat.

Here is an example beat:

```python
import wubwub as wb
import wubwub.sounds as snd

# load sounds
DRUMS = snd.load('drums.808')

# create a sequencer and add tracks
seq = wb.Sequencer(bpm=120, beats=8)
kick = seq.add_sampler(DRUMS['kick1'], name='Kick')
clap = seq.add_sampler(DRUMS['handclap'], name='Clap')
hat = seq.add_sampler(DRUMS['closed_hihat'], name='HiHat')
rim = seq.add_sampler(DRUMS['rimshot'], name='Rim')

# add notes
kick.make_notes_every(1)
clap.make_notes_every(2, offset=1)
hat.make_notes_every(.5)
rimpattern = wb.Pattern([1, 1.25, 1.5,
                         2,
                         3, 3.25, 3.75,
                         4, 4.5], length=4)
rim[rimpattern * 2] = wb.Note()

```

Sequencers have a `wubwub.sequencer.Sequencer.show()` method, which
calls `seqstring()` and prints the output.

```python
>>> seq.show()
      1 2 3 4 5 6 7 8
 Kick ■ ■ ■ ■ ■ ■ ■ ■
 Clap □ ■ □ ■ □ ■ □ ■
HiHat ■ ■ ■ ■ ■ ■ ■ ■
  Rim ■ ■ ■ ■ ■ ■ ■ ■

```

By default, the seqstring's resolution is equal to the `beats` attribute
of the Sequencer.  The Track names are determined by the `name` attribute
of each Track.

You can increase the resolution to see the hihat and rimshot patterns:

```python
>>> seq.show(resolution = 1/4)
      1       2       3       4       5       6       7       8
 Kick ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □
 Clap □ □ □ □ ■ □ □ □ □ □ □ □ ■ □ □ □ □ □ □ □ ■ □ □ □ □ □ □ □ ■ □ □ □
HiHat ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □
  Rim ■ ■ ■ □ ■ □ □ □ ■ ■ □ ■ ■ □ ■ □ ■ ■ ■ □ ■ □ □ □ ■ ■ □ ■ ■ □ ■ □

```
Note that `1/4` here means 1/4 of each beat in the Sequencer; not a "quarter note".
Since this beat is basically common time, `1/4` is essentially sixteenth-notes.

You can change the symbols used, for beats with one note, multiple notes,
or no notes:

```python
>>> seq.show(singlenote='.', multinote = 'o', empty = ' ')
      1 2 3 4 5 6 7 8
 Kick . . . . . . . .
 Clap   .   .   .   .
HiHat o o o o o o o o
  Rim o . o o o . o o

```

You can also set the wrap length (the number of boxes per line, as determined
by the `resolution`):

```python
>>> seq.show(resolution=1/4, wrap=16)
      1       2       3       4          \\
 Kick ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □
 Clap □ □ □ □ ■ □ □ □ □ □ □ □ ■ □ □ □
HiHat ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □
  Rim ■ ■ ■ □ ■ □ □ □ ■ ■ □ ■ ■ □ ■ □

      5       6       7       8
 Kick ■ □ □ □ ■ □ □ □ ■ □ □ □ ■ □ □ □
 Clap □ □ □ □ ■ □ □ □ □ □ □ □ ■ □ □ □
HiHat ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □ ■ □
  Rim ■ ■ ■ □ ■ □ □ □ ■ ■ □ ■ ■ □ ■ □

```

"""

import numpy as np

from wubwub.errors import WubWubError

def seqstring(sequencer, name_cutoff=None, resolution=1, singlenote='■',
              multinote='■', empty='□', wrap=32):
    '''
    Create a string diagram of a Sequencer.  The diagram is essentially
    a boolean grid, where the rows are Tracks and the columns are beats.
    Cells are filled when the given Track contains a Note/Chord on the given
    beat.

    Parameters
    ----------
    sequencer : wubwub.sequencer.Sequencer
        A Sequencer.
    name_cutoff : int, optional
        Number of characters to allow track names to be. The default is None.
    resolution : int or float, optional
        Determines the frequency of beats to use. The default is 1.
    singlenote : str, optional
        Character to use for beats containing single Notes. The default is '■'.
    multinote : str, optional
        Character to use for beats containing multiple notes. The default is '■'.
    empty : str, optional
        Character to use for beats not containing notes. The default is '□'.
    wrap : int, optional
        How many beats (as determined by `resolution`) to show on a single line.
        The default is 32.

    Raises
    ------
    WubWubError
        The resolution does not evenly divide 1.

    Returns
    -------
    str
        The string diagram.

    '''
    tracknames = []
    namelengths = []
    for track in sequencer.tracks():
        n = track.name
        if name_cutoff and len(track.name) > name_cutoff:
            n = track.name[:-4] + '...'

        tracknames.append(n)
        namelengths.append(len(n))

    if ((1 / resolution) % 1) != 0:
        raise WubWubError('`resolution` must evenly divide 1')

    steps = int(sequencer.beats * (1 / resolution))
    beats = np.linspace(1, sequencer.beats + 1, steps, endpoint=False)

    namespacing = max(namelengths)
    beatspacing = len(str(sequencer.beats)) + 1

    chunks = [beats[i:i + wrap] for i in range(0, len(beats), wrap)]
    strings = []

    boxarray = np.zeros((len(sequencer.tracks()), steps))

    for i, track in enumerate(sequencer.tracks()):
        unpacked = track.unpack_notes()
        for beat, note in unpacked:
            start = int((beat-1) // resolution)
            boxarray[i, start] += 1

    boxarray[boxarray > 2] = 2
    conversiondict = {0 : empty,
                      1 : singlenote,
                      2 : multinote}

    idx = 0
    for i, chunk in enumerate(chunks):
        s = ''
        labelbeats = (chunk == chunk.astype(int))
        labels = np.where(labelbeats,
                          chunk.astype(int).astype(str),
                          '')

        beat_header = ''.join([j.rjust(beatspacing) for j in labels])
        beat_header = ' ' * namespacing + beat_header
        s += beat_header

        if i != len(chunks) - 1:
            s += '    \\'

        s += '\n'

        for j, (name, track) in enumerate(zip(tracknames, sequencer.tracks())):
            s += name.rjust(namespacing)
            arraysection = boxarray[j, idx:idx+len(chunk)]
            s += ''.join(conversiondict[a].rjust(beatspacing)
                         for a in arraysection)

            s += '\n'

        s += '\n'
        strings.append(s)
        idx += len(chunk)

    return ''.join(strings).strip('\n')



