# Examples

```python
import wubwub as wb
```

## Making Notes

Notes are initialized with a pitch, length, and volume.

```python
# the most generic note
n = wb.Note(pitch=0, length=1, volume=0)
```

**Pitch** can be any number (positive or negative, integer or float), which represents the amount of semitones to shift the pitch of the sample being played.  It can instead be in [scientific pitch notation](https://en.wikipedia.org/wiki/Scientific_pitch_notation), in which case it should be a `str` of a single capital letter corresponding to the pitch, an optional sharp (`#`) or flat (`b`), and a number representing the octave.  E.g:

- Middle C: `"C4"`
- 1st D sharp above middle C: `"D#4"`
- 2nd A flat below middle C: `"Ab2"`
- A very high G: `"G9"`

Using scientific pitch is only really useful if you know the original pitch of the sample (wubwub cannot detect it automatically).  In this case, you will typically set the `basepitch` attribute of the Track associated with the sample:

```python
seq = wb.Sequencer(bpm=120, beats=8)

# load a sample and encode its true pitch
seq.add_sampler(sample='piano_A4.wav', basepitch='A4', name='piano')
```

But for other instruments (particularly drums and sound effects), working with relative pitch in semitones is more straightforward.

**Length** is the length of the note in *beats*.  How long one beat is is dependent on the BPM of the Sequencer.

**Volume** is the amount of decibels to change the volume of the sample (negative or positive).  So `volume=0` means the volume of the sample will not be changed (not that it will be inaudible).

## Notes are immutable

Once a note is initialized, it cannot be changed.

```python
n = wb.Note(pitch=0)
n.pitch = 2
# AttributeError: 'Note' object doesn't support item assignment
```

In adding Notes to tracks, you are basically inserting a reference to a particular Note with a set pitch, length, and volume.  Because of this, you can add one Note object to multiple Tracks and not have to worry about the object being altered:

```python
seq = wb.Sequencer(bpm=120, beats=8)

seq.add_sampler(sample='synth1.wav', name='synth')
seq.add_sampler(sample='saxophone.wav', name='sax')

longnote = wb.Note(length=8, volume=2)
seq['synth'][1] = note
seq['sax'][1] = note

# if you could change the Note in synth1, it would change the note in synth2
```

To change a Note, you have to overwrite it:

```python
seq['synth'][1] = wb.Note(pitch=4, length=4, volume=1)
```

There is an `alter` method for producing a similar Note from an existing one:

```python
seq['sax'][1] = seq['sax'][0].alter(volume=0)
# the length is still 8, but the volume has been changed from 2 to 0
```

Two different Notes will be seen as equal if their pitch, volume, and length, are all equal:

```python
a = wb.Note(pitch=0, length=4, volume=1)
b = wb.Note(pitch=3, length=4, volume=1)

a == b # False
a == b.alter(pitch=0) # True
a == b.alter(pitch='C4') # False
a.alter(pitch='Bb2') == b.alter(pitch='Bb2') # True
```

## Chords

Chords are essentially a list of Notes.  They indicate that multiple Notes should be played at the same time on a given beat.  You can make a Chord by gathering a few Notes:

```python
amaj = wb.Chord([
  wb.Note('A4'),
  wb.Note('C#5'),
  wb.Note('E5')
])
```

You can also add Notes together to similar effect:

```python
cmin = wb.Note('C5') + wb.Note('Eb5') + wb.Note('G5')
```

The Notes are store as a [SortedList](http://www.grantjenks.com/docs/sortedcontainers/sortedlist.html), in order to ensure equivalence when comparing two Chords:

```python
amaj.notes
 # SortedKeyList([Note(pitch=A4, length=1, volume=0), Note(pitch=C#5, length=1, volume=0), Note(pitch=E5, length=1, volume=0)], key=<function Chord.__init__.<locals>.keyfunc at 0x7fb6edc03430>)
```

Some other dunder methods are implemented:

```python
amaj == cmin # False, checks if all the Notes of each Chord are equal
len(amaj)    # 3, the number of Notes
iter(amaj)   # for iterating over the Notes of a Chord
amaj[0]      # retrieve the first Note of the Chord
```

You can also add Chords to produce new ones:

```python
chord1 = wb.Note('D3') + wb.Note('F3')
chord2 = wb.Note('A3') + wb.Note('C4')
dmin7 = chord1 + chord2
```

Like Notes, Chords are also immutable.

## Arpchord

There is an additional type of Chord (literally a subclass) called an ArpChord.  It is mainly intended to be used with the Arpeggiator Track.  The main difference between a Chord and an ArpChord is that an ArpChord also has a length for the whole chord:

```python
notes = [wb.Note('D3'), wb.Note('F3'), wb.Note('A3'), wb.Note('C4')]
arp = wb.ArpChord(notes, length=4)
```

Even if the individual Notes that make up an ArpChord have different lengths, this length attribute will be used when playing back the arpeggiation.

A normal Chord can also be converted to an ArpChord:

```python
>>> wb.ArpChord(dmin7, length=3)
ArpChord(pitches=['D3', 'F3', 'A3', 'C4'], length=3)
```
