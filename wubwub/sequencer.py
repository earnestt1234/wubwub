#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains the Sequencer class, and associated functions for
working with Sequencers in wubwub.
"""

import os
import time

import pydub

from wubwub.audio import add_effects, play, _overhang_to_milli
from wubwub.errors import WubWubError
from wubwub.plots import sequencerplot
from wubwub.resources import MINUTE, unique_name
from wubwub.seqstring import seqstring
from wubwub.tracks import Sampler, Arpeggiator, MultiSampler

__all__ = ['Sequencer', 'stitch', 'join', 'loop']

class Sequencer:
    '''
    The Sequencer is the main tool for creating beats in wubwub.  Sequencers
    hold and organize individual instrument Tracks which can be filled
    with musical elements.  Sequencers have a defined length (and tempo), but
    multiple can be combined to create longer/varied arrangements.

    Both parameters for initialization (BPM and length) can be tweaked
    after creation by setting the value of the <code>bpm</code> or
    <code>beats</code> attributes.

    Parameters
    ----------
    bpm : int or float
        Tempo of the sequencer (beats per minute).
    beats : int
        The length of the sequence, in beats.

    Examples
    --------
    Initialize a Sequencer with a tempo and length:

    ```python
    >>> import wubwub as wb
    >>> seq = wb.Sequencer(bpm=120, beats=8)
    >>> seq
    Sequencer(bpm=120, beats=8, tracks=0)

    ```
    '''

    def __init__(self, bpm, beats):
        """Initialization function for the Sequencer.  Sets the BPM and beats
        based on user input, also defaults attributes related to post-processing
        the output audio and creates a container for subsidiary tracks."""

        self.bpm = bpm
        self.beats = beats

        self.effects = None
        self.volume = 0
        self.pan = 0
        self.postprocess_steps = ['effects', 'volume', 'pan']

        self._tracks = []

    def __repr__(self):
        """String representation of self."""
        l = len(self.tracks())
        return f"Sequencer(bpm={self.bpm}, beats={self.beats}, tracks={l})"

    def __getitem__(self, name):
        """Allows for retrieval of Track objects by their string name."""
        if not isinstance(name, str):
            e = f'Can only index Sequencer with str, not {type(name)}'
            raise WubWubError(e)
        return self.get_track(name)

    def _add_track(self, track):
        """Helper function called when adding a new track to self.  Checks for
        duplicate names, and tries to ensure non-duplicate entries of items
        in different Sequencers."""
        if track.name in self.tracknames():
            raise WubWubError(f'Track name "{track.name}" already in use.')
        if track.sequencer != self:
            track.sequencer = self
        if track not in self._tracks:
            self._tracks.append(track)

    def copypaste_section(self, start, stop, newstart):
        '''
        For all tracks of the Sequencer, take a section of notes and replicate
        them on a new beat (keeping the same relative spacing between notes).
        Simply, this method calls `wubwub.tracks.Track.copypaste()`
        for all tracks within the Sequencer.

        Parameters
        ----------
        start : int or float
            Beat to start copying notes (inclusive).
        stop : int or float
            Beat to stop copying notes (exlcusive).
        newstart : int or float
            Beat to paste the copied section.

        Returns
        -------
        None.

        '''
        for track in self.tracks():
            track.copypaste(start, stop, newstart)

    def set_beats_and_clean(self, new):
        """
        Modifies the Sequencer length while simultaneously removing notes
        that are outside of the sequence after the change.  I.e., sets
        <code>beats</code> and calls `wubwub.tracks.Track.clean()` for
        all tracks.  This is a convenience method which is only useful when
        shortening the sequence length.

        Parameters
        ----------
        new : int
            New value for the length of the Sequencer.

        Returns
        -------
        None.

        """
        self.beats = new
        for track in self.tracks():
            track.clean()

    def get_track(self, track):
        '''
        Return a Track, keyed by either its name or the Track
        itself (provided the Track is part of the current Sequencer).

        Parameters
        ----------
        track : str or Track
            Handle for a Track to retrieve.

        Raises
        ------
        ValueError
            Track not found.

        Returns
        -------
        Track
            A track that is part of this Sequencer.

        '''
        if isinstance(track, str):
            try:
                return next(t for t in self._tracks if t.name == track)
            except:
                raise ValueError(f'no track with name {track}')
        elif track in self._tracks:
            return track
        else:
            raise ValueError('Requested track is not part of sequencer.')

    def tracks(self):
        """Returns a tuple of the Track objects currently part of this Sequencer."""
        return tuple(self._tracks)

    def tracknames(self):
        """Returns a list of the names of each Track currenlty part of this Sequencer."""
        return [t.name for t in self._tracks]

    def add_sampler(self, sample, name=None, overlap=False, basepitch='C4'):
        """
        Create a new `wubwub.tracks.Sampler` Track and add to the Sequencer.
        Parameters here are initialization values for `wubwub.tracks.Sampler`;
        see there for more detailed documentation.

        Parameters
        ----------
        sample : path or pydub.AudioSegment
            Sample for Sampler initialization.
        name : str, optional
            Name for the new Sampler.
        overlap : bool, optional
            Set the overlap behavior of the new Sampler. The default is False.
        basepitch : int or str, optional
            Set the base pitch for the new Sampler. The default is 'C4'.

        Returns
        -------
        new : wubwub.tracks.Sampler
            The new Track.

        Examples
        --------
        ```python
        import wubwub as wb

        seq = wb.Sequencer(bpm=100, beats=16)

        # path to sound
        seq.add_sampler('my_kick.wav', name='kick')

        # using a pydub.AudioSegment
        import wubwub.sounds as snd

        clap = snd.load('drums.808')['handclap']
        seq.add_sampler(clap, name='clap')
        ```

        """
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = Sampler(name=name, sample=sample, overlap=overlap,
                      basepitch=basepitch, sequencer=self)
        return new

    def add_arpeggiator(self, sample, name=None, freq=0.5, method='up',
                        basepitch='C4'):
        '''
        Create a new `wubwub.tracks.Arpeggiator` Track and add to the Sequencer.
        Parameters here are initialization values for `wubwub.tracks.Arpeggiator`;
        see there for more detailed documentation.

        Parameters
        ----------
        sample : path or pydub.AudioSegment
            Sample for Sampler initialization.
        name : str, optional
            Name for the new Sampler.
        freq : int or float, optional
            Set the frequency of the new arpeggiator. The default is 0.5.
        method : str, optional
            Set the pattern of the new arpeggiator. The default is 'up'.
        basepitch : int or str, optional
            Set the base pitch for the new Sampler. The default is 'C4'.

        Returns
        -------
        new : wubwub.tracks.Arpeggiator
            The new Track.

        Examples
        --------
        ```python
        import wubwub as wb

        seq = wb.Sequencer(bpm=100, beats=16)

        # path to sound, or a pydub.AudioSegment
        seq.add_arpeggiator('saw.wav', name='Arp', freq=.5, method='downup')
        ```

        '''
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = Arpeggiator(name=name, sample=sample, freq=freq,
                          method=method, basepitch=basepitch,
                          sequencer=self)
        return new

    def add_multisampler(self, name=None, overlap=False):
        '''
        Create a new `wubwub.tracks.MultiSampler` Track and add to the Sequencer.
        Parameters here are initialization values for `wubwub.tracks.MultiSampler`;
        see there for more detailed documentation.

        Parameters
        ----------
        name : str, optional
            Name for the new Sampler.
        overlap : bool, optional
            Set the overlap behavior of the new Sampler. The default is False.

        Returns
        -------
        new : wubwub.tracks.MultiSampler
            The new Track.

        '''
        if name is None:
            name = unique_name('Track', self.tracknames())
        new = MultiSampler(name=name, overlap=overlap, sequencer=self)
        return new

    def add_samplers(self, samples, names=None, overlap=False, basepitch='C4'):
        '''
        From a list of sounds or pydub Audio Segments, add multiple
        `wubwub.tracks.Sampler` Tracks.

        Parameters
        ----------
        samples : list like
            List of paths to sounds, or pydub AudioSegments to load.
        names : list like, optional
            The string name of each sample being added. The default is None.
        overlap : bool, optional
            The overlap behavior of the new samplers. The default is False.
        basepitch : int or str, optional
            The base pitch of the new samplers. The default is 'C4'.

        Returns
        -------
        None.

        '''
        if names is None:
            names = [None] * len(samples)
        for sample, name in zip(samples, names):
            self.add_sampler(sample=sample, name=name, overlap=overlap,
                             basepitch=basepitch)

    def duplicate_track(self, track, newname=None, with_notes=True):
        '''
        Create a copy of the specified Track within and add it to the
        current Sequencer.

        Parameters
        ----------
        track : wubwub.tracks.Track or str
            Name of a Track, or the actual Track object.
        newname : str, optional
            New name for the duplicated Track. The default is None.  If not passed,
            a generic name is created.
        with_notes : bool, optional
            When True (default), all the Notes/Chords contained in the original
            Track are copied over.

        Returns
        -------
        dup : wubwub.tracks.Track
            Reference to the new Track.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        # add a track with some notes
        >>> seq = wb.Sequencer(bpm=120, beats=8)
        >>> seq.add_sampler(snd.load('drums.808')['kick1'], name='kick1')
        >>> seq['kick1'].make_notes_every(1)

        # duplicate the track
        >>> seq.duplicate_track('kick1', newname='kick2')

        # by default, the notes are copied
        >>> len(seq['kick2'].notedict)
        8

        # specify with_notes to change this behavior
        >>> seq.duplicate_track('kick1', newname='kick3', with_notes=False)
        >>> len(seq['kick3'].notedict)
        0
        ```

        '''
        if newname is None:
            newname = unique_name('Track', self.tracknames())
        dup = self.get_track(track).copy(newname=newname, with_notes=with_notes)
        return dup

    def copy(self, with_notes=True):
        '''
        Create a copy of the current Sequencer.  The copy (and its associated
        Tracks) are *new objects*, so editing it will not affect this Sequencer
        (and vice versa).


        Parameters
        ----------
        with_notes : bool, optional
            When True (default), all the Notes/Chords are copied over for
            every copied track.

        Returns
        -------
        new : wubwub.sequencer.Sequencer
            The new Sequencer.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        # add a track
        >>> seq = wb.Sequencer(bpm=120, beats=8)
        >>> seq.add_sampler(snd.load('drums.808')['kick1'], name='kick1')

        # copy the sequencer
        >>> other = seq.copy()

        # editing the new sequencer doesn't affect the original
        >>> other.delete_track('kick1')
        >>> other.tracknames()
        []

        >>> seq.tracknames()
        ['kick1']
        ```

        '''
        new = Sequencer(beats=self.beats, bpm=self.bpm)
        for track in self.tracks():
            track.copy(with_notes=with_notes, newseq=new)
        return new

    def split(self, beat):
        '''
        Split the Sequencer into two new Sequencers at a given beat.  The objects
        returned are *new Sequencers* (generated by `Sequencer.copy()`).

        Parameters
        ----------
        beat : int
            The beat to split the Sequencer on.

        Raises
        ------
        TypeError
            Non-integer beat is passed.

        Returns
        -------
        a, b : wubwub.sequencer.Sequencer
            Two new Sequencers.

        Examples
        --------
        ```python
        >>> import wubwub as wb
        >>> import wubwub.sounds as snd

        # make a sequencer and add tracks/notes
        >>> seq = wb.Sequencer(beats=8, bpm=100)
        >>> drums = snd.load('drums.808')
        >>> kick = seq.add_sampler(drums['kick1'], name='kick')
        >>> snare = seq.add_sampler(drums['snare'], name='snare')
        >>> kick.make_notes_every(2)
        >>> snare.make_notes_every(2, offset=1)
        >>> seq.show()
              1 2 3 4 5 6 7 8
         kick ■ □ ■ □ ■ □ ■ □
        snare □ ■ □ ■ □ ■ □ ■

        # split
        >>> a, b = seq.split(4)

        # show
        >>> a.show()
              1 2 3
         kick ■ □ ■
        snare □ ■ □

        >>> b.show()
              1 2 3 4 5
         kick □ ■ □ ■ □
        snare ■ □ ■ □ ■
        ```

        '''
        if not isinstance(beat, int):
            raise TypeError(f'Beat for split must be int, not {type(beat)}.')

        a1, a2 = (1, beat)
        b1, b2 = (beat, self.beats+1)

        a = self.copy(with_notes=False)
        a.beats = a2 - a1
        b = self.copy(with_notes=False)
        b.beats = b2 - b1

        for selftrack, atrack, btrack in zip(self.tracks(), a.tracks(), b.tracks()):
            anotes = selftrack.slice[a1:a2]
            atrack.add_fromdict(anotes)
            bnotes = selftrack.slice[b1:b2]
            btrack.add_fromdict(bnotes, offset=(-beat + 1))

        return a, b

    def delete_track(self, track):
        """
        Delete a Track from the Sequencer, along with any entered Notes.

        Parameters
        ----------
        track : str or wubwub.tracks.Track
            Reference to the Track to delete.

        Returns
        -------
        None.

        """
        t = self.get_track(track)
        t.sequencer = None
        self._tracks.remove(t)

    def build(self, overhang=0, overhang_type='beats'):
        '''
        Render all the contained Tracks into one output, namely a pydub
        AudioSegment.  Calls the "build" method of each Track, and overlays
        them.

        Parameters
        ----------
        overhang : int or number, optional
            How much extra time to render beyond the length
            (i.e., the `beats`) of the Sequencer. The default is 0.
            Units are either in beats or in seconds, dependent on the
            `overhang_type` argument.  This can be useful when there are
            notes or effects that reverberate beyond the duration of the
            Sequencer.
        overhang_type : str -> "beats" or "seconds", optional
            Unit for the overhang. The default is 'beats'.

        Returns
        -------
        pydub.AudioSegment
            The rendered audio.

        Examples
        --------
        ```python
        >>> import wubwub as wb

        # 60 BPM == 1 second per beat
        >>> seq = wb.Sequencer(beats=4, bpm=60)

        # expected length (in milliseconds, per pydub)
        >>> expected = 4 * 1000
        >>> expected == len(seq.build())
        True

        # add overhang of 2 beats
        >>> len(seq.build(overhang=2))
        6000

        # add overhang in seconds
        >>> len(seq.build(overhang=3.777, overhang_type='beats'))
        7777
        ```

        '''
        b = (1/self.bpm) * MINUTE
        seq_oh = _overhang_to_milli(overhang, overhang_type, b)
        tracklength = self.beats * b + seq_oh
        audio = pydub.AudioSegment.silent(duration=tracklength)
        for track in self.tracks():
            audio = audio.overlay(track.build(overhang, overhang_type))
        return self.postprocess(audio)

    def postprocess(self, build):
        '''
        Add postprocessing to a rendered audio output of the Sequencer,
        typically that of `Sequencer.build()`.  There are currently 3
        postprocessing steps applied, corresponding to 3 attributes of
        the Sequencer:

        - `effects`: This attribute can be set to a pysndfx
        AudioEffectsChain instance to add audio effects (such as reverb,
        delay, overdrive, etc.) See
        [here](https://github.com/carlthome/python-audio-effects) for more
        documentation.
        - `volume`: This attribute can be set to modify the output volume
        of the build.  Note that the value reflects a relative change in
        dB, so values can be positive or negative.
        - `pan`: a value between `-1.0` (100% left) and `+1.0` (100% right)
        indicating the stereo panning (`0.0` is centered).

        The order/presence of these processing steps can be determined by
        setting the `postprocess_steps` attribute, which should be a list
        containing some subset of the strings `'effects'`, `'volume'`, and
        `'pan`' (corresponding to each of the three steps above).  The default
        is `self.postprocess_steps = ['effects', 'volume', 'pan']`.  *Omitted
        steps in this attribute will not be applied, while repeated steps
        will be applied multiple times.*  Additionally, the steps are applied
        in the order encountered in `self.postprocess_steps`.

        Parameters
        ----------
        build : pydub AudioSegment
            Audio to postprocess, typically output of `Sequencer.build()`

        Returns
        -------
        build : pydub AudioSegment
            Audio with postprocessing steps applied.

        '''
        for step in self.postprocess_steps:
            if step == 'effects':
                build = add_effects(build, self.effects)
            if step == 'volume':
                build += self.volume
            if step == 'pan':
                build = build.pan(self.pan)
        return build

    def play(self, start=1, end=None, overhang=0, overhang_type='beats'):
        '''
        Audio playback of the Sequencer.

        Parameters
        ----------
        start : int, optional
            Beat to start playback on. The default is 1.
        end : int or None, optional
            Beat to end playback on. The default is None.
        overhang : int or number, optional
            How much extra time to render beyond the length
            (i.e., the `beats`) of the Sequencer. The default is 0.
            Units are either in beats or in seconds, dependent on the
            `overhang_type` argument.  This can be useful when there are
            notes or effects that reverberate beyond the duration of the
            Sequencer.
        overhang_type : str -> "beats" or "seconds", optional
            Unit for the overhang. The default is 'beats'.

        Returns
        -------
        None.

        '''
        b = (1/self.bpm) * MINUTE
        start = (start-1) * b
        if end is not None:
            end = (end-1) * b
        build = self.build(overhang, overhang_type)
        play(build[start:end])

    def loop(self, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
        '''
        Return a looped rendering of the Sequencer.  This is akin to
        `Sequencer.build()`, but the content of the Sequencer is repeated
        a specified number of times.

        Parameters
        ----------
        times : int, optional
            How many times to loop. The default is 4.
        internal_overhang : int or float, optional
            Determine the length of extra time to render when the loop restarts.
            This can be used to prevent abrubt shortening of sounds near the
            end of the sequence. The default is 0, meaning all sounds are
            cut at the end of the Sequencer length for each loop.
        end_overhang : int or float, optional
            Determine the length of extra time to render at the of the audio,
            i.e. after all loops are complete. The default is 0.
        overhang_type : str -> 'beats' or 'seconds', optional
            Units for the overhang. The default is 'beats'.

        Returns
        -------
        looped : pydub.AudioSegment
            The looped audio.

        '''
        looped = loop(self, times=times, internal_overhang=internal_overhang,
                      end_overhang=end_overhang, overhang_type=overhang_type)
        return looped

    def loopplay(self, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
        '''Calls `Sequencer.play()` on `Sequencer.loop()`; i.e.
        immediately plays back looped audio.'''
        looped = loop(self, times=times, internal_overhang=internal_overhang,
                      end_overhang=end_overhang, overhang_type=overhang_type)
        play(looped)

    def soundtest(self, selection=None, postprocess=True, gap=.5):
        '''Calls the sound test method for each Track in the Sequencer; i.e.
        plays back all the samples being used.'''
        if selection is None:
            selection = self.tracks()
        else:
            selection = [self.get_track(i) for i in selection]

        for track in selection:
            print(f'Playing sample(s) for "{track.name}"...')
            time.sleep(.25)
            track.soundtest(postprocess=postprocess)
            time.sleep(gap)

    def export(self, path, overhang=0, overhang_type='beats'):
        '''
        Saves the rendered audio to a file.  The Sequencer creates
        a pydub AudioSegment which contains all Tracks overlaid,
        and then uses its export method to save.

        See the pydub documentation for more information on exporting.

        Parameters
        ----------
        path : system path
            File path to save the audio to.
        overhang : int or number, optional
            How much extra time to render beyond the length
            (i.e., the `beats`) of the Sequencer. The default is 0.
            Units are either in beats or in seconds, dependent on the
            `overhang_type` argument.  This can be useful when there are
            notes or effects that reverberate beyond the duration of the
            Sequencer.
        overhang_type : str -> "beats" or "seconds", optional
            Unit for the overhang. The default is 'beats'.

        Returns
        -------
        None.

        '''
        _, fmt = os.path.splitext(path)
        build = self.build(overhang, overhang_type)
        build.export(path, format=fmt)

    def show(self, printout=True, name_cutoff=None, resolution=1,
             singlenote='■', multinote='■', empty='□', wrap=32):
        '''
        Print (or return) a sequencer grid diagram, showing when
        each Track contains notes.  For more information, see
        `wubwub.seqstring.seqstring()`.

        Parameters
        ----------
        printout : bool, optional
            When True (default), print the diagram.  When False,
            return the string.
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

        Returns
        -------
        s (str) or None
            The string diagram is returned if `printout` is `False`, otherwise
            it is printed and `None` is returned.

        '''
        s = seqstring(self,
                      name_cutoff=name_cutoff,
                      resolution=resolution,
                      singlenote=singlenote,
                      multinote=multinote,
                      empty=empty,
                      wrap=wrap)
        if printout:
            print(s)
        else:
            return s

    def plot(self, timesig=4, grid=True, ax=None, scatter_kwds=None,
             plot_kwds=None):
        '''
        Run `wubwub.plots.sequencerplot()` for this Sequencer.

        timesig : int, optional
            Sets the ticks/grid to a given frequency of beats. The default is 4.
        grid : bool, optional
            Whether to include a grid. The default is True.
        ax : matplotlib.axes.Axes, optional
            Axes to create the plot on. The default is None.
        scatter_kwds : dict, optional
            Keyword arguments passed to `matplotlib.axes.Axes.scatter`.
            The default is None.
        plot_kwds : dict, optional
            Keyword arguments passed to `matplotlib.axes.Axes.plot`.
            The default is None.

        Returns
        -------
        matplotlib.figure.Figure
            The Figure containing the axes used.

        '''
        return sequencerplot(self,
                             timesig=timesig,
                             grid=grid,
                             ax=ax,
                             scatter_kwds=scatter_kwds,
                             plot_kwds=plot_kwds)


def stitch(sequencers, internal_overhang=0, end_overhang=0, overhang_type='beats'):
    """
    Take a list of Sequencers, and concatenate the audio produced by each one.
    A pydub `AudioSegment` is returned, which is the concatenation of
    the outputs of each Sequencer's `build()` method.

    Parameters
    ----------
    sequencers : list-like
        Sequencers to use.
    internal_overhang : int or float, optional
        Determine the length of extra time to render when the loop restarts.
        This can be used to prevent abrubt shortening of sounds near the
        end of the sequence. The default is 0, meaning all sounds are
        cut at the end of the Sequencer length for each loop.
    end_overhang : int or float, optional
        Determine the length of extra time to render at the of the audio,
        i.e. after all loops are complete. The default is 0.
    overhang_type : str -> 'beats' or 'seconds', optional
        Units for the overhang. The default is 'beats'.

    Returns
    -------
    stitched : pydub.AudioSegment
        AudioSegment of the stitched audio.

    Examples
    --------

    ```python
    import wubwub as wb

    # init some dummy Sequencers
    a = wb.Sequencer(beats=8, bpm=120)
    b = wb.Sequencer(beats=4, bpm=120)

    # stitch is used to concatenate their audio (empty here)
    stitched = wb.stitch([a, b])

    # with no end_overhang, the length should be equal to the sum of lengths
    print(len(stitched) == len(a.build()) + len(b.build()))
    # True

    ```

    """
    total_length = 0
    current = 0
    sectionstarts = []
    for seq in sequencers:
        b = (1/seq.bpm) * MINUTE
        seq_length = b * seq.beats
        total_length += seq_length
        sectionstarts.append(current)
        current += seq_length
    total_length += _overhang_to_milli(end_overhang, overhang_type, b)

    stitched = pydub.AudioSegment.silent(duration=total_length)
    for start, seq in zip(sectionstarts, sequencers):
        build = seq.build(internal_overhang, overhang_type)
        stitched = stitched.overlay(build, start)

    return stitched

def _matchesforjoin(oldtracks, newtrack, on='name'):
    '''Helper method for joining two Sequencers.  Given a list of tracks
    (from one Sequencer) and a test track (from a different Sequencer), tries
    to return a matching track.'''
    ons = ['name', 'sample', 'sample+type']
    if on not in ons:
        raise WubWubError(f'`on` must be selected from {ons}')

    if on == 'name':
        return [track for track in oldtracks if track.name == newtrack.name]
    if on == 'sample':
        return [track for track in oldtracks if track.sample == newtrack.sample]
    if on == 'sample+type':
        return [track for track in oldtracks if track.sample == newtrack.sample
                and type(track) == type(newtrack)]
    return []

def join(sequencers, on='name'):
    '''
    Combine multiple Sequencers into a single Sequencer.  The function
    tries to match Tracks based on either the name or sample (see the `on`
    parameter).  If a Track cannot be matched, it is kept as a separate
    entity. This hopefully works well for re-merging Sequencers created
    by `split()`, but may not work as well when merging very different
    Sequencers (please report any issues).

    Parameters
    ----------
    sequencers : list-like
        List of Sequencers to join.
    on : str, "name", "sample", or "sample+type", optional
        Method to use for matching Tracks between adjacent Sequencers.
        If 'name' (default), match based on the Track name.  If 'sample',
        match based on equivalence of the `sample` attribute. If `sample+type`,
        match based on the sample, but also on the Track being of the same
        class.

    Returns
    -------
    out : wubwub.sequencer.Sequencer
        The joined Sequencers.

    '''
    beats = sum(seq.beats for seq in sequencers)
    out = Sequencer(bpm=sequencers[0].bpm, beats=beats)
    offset = 0
    for i, seq in enumerate(sequencers):
        oldtracks = out.tracks()
        available = list(oldtracks)

        for track in seq.tracks():
            match = None
            matches = _matchesforjoin(available, track, on=on)
            if matches:
                match = matches[0]
                available.remove(match)

            if match:
                match.add_fromdict(track.notedict, offset=offset)

            else:
                new = track.copy(with_notes=False, newseq=out)
                new.add_fromdict(track.notedict, offset=offset)


        offset = seq.beats
    return out

def loop(sequencer, times=4, internal_overhang=0, end_overhang=0, overhang_type='beats'):
    '''Calls `stitch()` on one Sequencer multiple times, to create a looped
    AudioSegment.'''

    return stitch([sequencer] * times,
                  internal_overhang,
                  end_overhang,
                  overhang_type)
