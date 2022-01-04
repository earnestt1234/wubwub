#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class for encoding rhythmic patterns.
"""

from sortedcontainers import SortedList

class Pattern:
    '''Class for encoding a rhythmic pattern.'''
    def __init__(self, pattern, length):
        '''Initialize with a list of beats and a length of the pattern (in beats).
        The `pattern` will be converted into a SortedList.'''
        self.pattern = SortedList(pattern)
        self.length = length

    def __repr__(self):
        '''String representation'''
        return f'Pattern(pattern={self.pattern}, length={self.length})'

    def __eq__(self, other):
        '''Returns True if the pattern and length of other equal that of self.'''
        return self.pattern == other.pattern and self.length == other.length

    def __iter__(self):
        '''Iterate over the beats in the pattern of self.'''
        return iter(self.pattern)

    def __add__(self, other):
        '''Create a new pattern with the beats of self followed by the beats of other.'''
        if not isinstance(other, Pattern):
            raise TypeError(f'Can only add Pattern with Pattern, not {type(other)}.')
        newp = self.pattern + [p + self.length for p in other.pattern]
        newl = self.length + other.length
        return Pattern(newp, newl)

    def __radd__(self, other):
        '''Create a new pattern with the beats of self followed by the beats of other.'''
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __iadd__(self, other):
        '''Add to the pattern of self.'''
        self.pattern += [p + self.length for p in other.pattern]
        self.length += other.length
        return self

    def __mul__(self, n):
        '''Repeat the pattern n times.'''
        if not isinstance(n, int):
            raise TypeError('Can only multiply Pattern by int, not {type(other)}.')
        newp = SortedList()
        newl = 0
        for i in range(n):
            newp += [p + newl for p in self.pattern]
            newl += self.length
        return Pattern(newp, newl)

    def __rmul__(self, n):
        '''Repeat the pattern n times.'''
        return self.__mul__(n)

    def __imul__(self, n):
        '''Repeat the pattern n times.'''
        if not isinstance(n, int):
            raise TypeError('Can only multiply Pattern by int, not {type(other)}.')
        newp = SortedList()
        newl = 0
        for i in range(n):
            newp += [p + newl for p in self.pattern]
            newl += self.length
        self.pattern = newp
        self.length = newl
        return self

    def __len__(self):
        '''Return the number of elements in the pattern of self.'''
        return len(self.pattern)

    def merge(self, other):
        '''
        Join a new pattern, keeping the union of beats and the maximum length.

        Parameters
        ----------
        other : Pattern
            New pattern to merge.

        Returns
        -------
        Pattern
            A new Pattern object.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        >>> a = wb.Pattern([1, 3, 5, 7], length=8)
        >>> b = wb.Pattern([6, 8], length=4)
        >>> a.merge(b)
        Pattern(pattern=SortedList([1, 3, 5, 6, 7, 8]), length=8)

        ```

        '''
        newp = self.pattern.copy()
        for p in other.pattern:
            if p not in newp:
                newp.add(p)
        newl = max(self.length, other.length)
        return Pattern(newp, newl)

    def on(self, beat):
        '''
        Create a new Pattern with the same rhythm as self but
        starting on a new beat.

        Parameters
        ----------
        beat : number
            New beat to start the pattern on.

        Returns
        -------
        Pattern
            New Pattern.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        >>> a = wb.Pattern([1, 1.25, 1.75, 2, 2.5], length=2)
        >>> a.on(42)
        Pattern(pattern=SortedList([42, 42.25, 42.75, 43, 43.5]), length=2)

        ```

        '''
        return Pattern([(beat-1) + p for p in self.pattern], self.length)

    def onmeasure(self, measure, measurelen=None):
        '''
        Shift a Pattern of given number of measures.

        Parameters
        ----------
        measure : int
            Measure number.
        measurelen : int, optional
            Number of beats in the measure. The default is None, in which case
            the Pattern length is used.

        Returns
        -------
        Pattern
            New Pattern.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        >>> a = wb.Pattern([1, 1.25, 1.75, 2, 2.5], length=2)
        >>> a.onmeasure(3, measurelen=4)
        Pattern(pattern=SortedList([9, 9.25, 9.75, 10, 10.5]), length=2)

        ```

        '''
        if measurelen == None:
            measurelen = self.length
        return self.on(1 + (measure - 1) * measurelen)

    def chop(self, beat):
        '''
        Keep only elements of the Pattern before a given beat.

        Parameters
        ----------
        beat : number
            Beat to chop on.  Also sets the length of the new Pattern.

        Returns
        -------
        Pattern
            A new Pattern.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        >>> a = wb.Pattern([1, 1.25, 1.5, 2, 3.25, 3.75, 4.25], length=4)
        >>> a.chop(3)
        Pattern(pattern=SortedList([1, 1.25, 1.5, 2]), length=2)

        ```

        '''
        newp = [p for p in self.pattern if p < beat]
        newl = beat - 1
        return Pattern(newp, newl)

    def copy(self):
        '''Return a copy of self.'''
        return Pattern(self.pattern, self.length)

    def until(self, beat):
        '''
        Repeat the current pattern until a certain beat.

        Parameters
        ----------
        beat : number
            Beat to repeat until.

        Returns
        -------
        Pattern
            New Pattern.

        Examples
        --------

        ```python
        >>> import wubwub as wb

        >>> a = wb.Pattern([1, 2, 3, 4], length=4)
        >>> a = wb.Pattern([1, 2, 3, 4], length=4)
        Pattern(pattern=SortedList([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]), length=16)

        ```

        '''
        repeats, extra = divmod(beat, self.length)
        return self.copy() * repeats + self.copy().chop(extra + 1)

