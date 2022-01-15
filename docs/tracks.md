# Tracks

Tracks are the primary interface for creating and editing musical arrangements at the level of an individual instrument or sound.  Sequencers (i.e. `wubwub.sequencer.Sequencer`) are populated with Tracks corresponding to instruments, and Tracks are populated with musical elements (notes and chords).  All Tracks in wubwub are some kind of *sampler*; they load in an audio file and play it back with various manipulations (in pitch, volume, length, etc.).  

The following documentation will cover some of the major ideas behind Tracks, giving examples along the way.

## Module structure

There is one major `wubwub.tracks.Track` class which outlines the major functionalities of Tracks and defines the methods common to all flavors of Tracks in wubwub.  Subclasses of this parent define more specific behaviors and constitute the objects which are actually interfaced with to make music.  There are three major types of Track available to the user:

- `wubwub.tracks.Sampler` is the most basic Track, which takes in a single sample.
- `wubwub.tracks.MultiSampler` is similar to the Sampler, but can assign samples to different pitches.
- `wubwub.tracks.Arpeggiator` is similar to the Sampler in that it takes in one sample, but has specific methods designed for chord arpeggiation.

## Creating Tracks

Expect in rare cases, a Track must be connected with a `wubwub.sequencer.Sequencer`.  The recommended approach is to initialize a Sequencer (i.e. a musical project/song) and then add Tracks (i.e. instruments/sounds) to it.  There are specific Sequencer methods for creating Tracks:

```python
>>> import wubwub as wb

>>> seq = wb.Sequencer(beats = 8, bpm = 100)
>>> kick = seq.add_sampler(sample='/my_samples/drums/kick.wav', name='kick')
>>> type(kick)
<class 'wubwub.tracks.Sampler'>

```

In the above example, a Sequencer `seq` is initialized, and then the `wubwub.sequencer.Sequencer.add_sampler()` method is called to create a new Track.  The Track is initialized by providing a path to an audio file (`sample`) and a string name for identifying the Track (`name`).  Since it was created with the `add_sampler()` method, the Track is already linked to the `seq` Sequencer object.

There are similar `wubwub.sequencer.Sequencer.add_multisampler()` and `wubwub.sequencer.Sequencer.add_arpeggiator()` methods for creating the other sorts of Tracks.  But this "getting started" section will focus on the simple Sampler for now.

The `sample` parameter can either be a system path to an audio file, or a [pydub `AudioSegment`](https://github.com/jiaaro/pydub) object (this is the type of object that the system paths are converted into).  The latter option is utilized when working with the samples provided by `wubwub.sounds`:

```python
>>> import wubwub.sounds as snd
>>> DRUMS = snd.load('drums.808')
>>> x = DRUMS['handclap'] # <class 'pydub.audio_segment.AudioSegment'>
>>> clap = seq.add_sampler(sample=x, name='clap')

```

## How to keep ... track

The Sequencer can help locate and manipulate its Tracks after creation.  You can use indexing syntax to retrieve Tracks by name:

```python
>>> seq['clap']
Sampler(name="clap")

```

You can check all the Tracks contained within:

```python
>>> seq.tracks()
(Sampler(name="kick"), Sampler(name="clap"))

>>> seq.tracknames()
['kick', 'clap']

```

There are several other methods documented under `wubwub.sequencer.Sequencer` which provide basic functionality for managing Tracks.  If you need to delete or duplicate a Track, respectively look at `wubwub.sequencer.Sequencer.delete_track()` and `wubwub.sequencer.Sequencer.duplicate_track()`.

A Track can also produce information about its parent Sequencer:

```python
# get the Sequencer itself
>>> clap.sequencer
Sequencer(bpm=60, beats=60, tracks=2)

# get the current BPM
>>> clap.get_bpm()
60

# or the number of beats
>>> clap.get_beats()
8

```

## The note dictionary 

All tracks have a `notedict` attribute for keeping track of musical directions.  It is initialized as an empty [SortedDict](http://www.grantjenks.com/docs/sortedcontainers/sorteddict.html):

```python
>>> kick.notedict()
SortedDict({})

```

Each Track has its own:

```python
>>> kick.notedict is clap.notedict
False

```

The keys for the `notedict` are numbers corresponding to sequencer pulses (i.e., musical beats), and the values are objects from the `wubwub.notes` module (i.e. "Notes" which determine the pitch, length, and volume of sample playback).  When playing back or exporting a song, each Track looks at its own notedict to decide when and how to play back samples.

## Adding notes

Most of the creation in wubwub involves writing to the note dictionary, and there are several options for doing so.  You can simply access the `notedict` attribute and add to it, but there are other approaches which are more versatile.

### Track specific methods

All Tracks have specific helper methods intended to simplify music writing.  For most of these, the user provides where to create notes (i.e. what beats); the function then construct the `wubwub.notes.Note` and `wubwub.notes.Chord` objects and add them to the note dictionary in the correct places:

```python
>>> kick.make_notes(beats = [1, 3, 5, 7])
>>> kick.pprint_notedict()
{1: Note(pitch=0, length=1, volume=0),
 3: Note(pitch=0, length=1, volume=0),
 5: Note(pitch=0, length=1, volume=0),
 7: Note(pitch=0, length=1, volume=0)}

```

The notes were added to the `kick` Track note dictionary on the desired `beats`, and initialized with default pitch, length, and volume values which can be set by `wubwub.tracks.SamplerLikeTrack.make_notes()`.  The values themselves are all some sort of relative measurement (pitch is semitones relative to the original sample, length is beats relative to the Sequencer BPM, and volume is decibels relative to the original sample).



