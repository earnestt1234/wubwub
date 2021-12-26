#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class for encoding rhythmic patterns.
"""

from sortedcontainers import SortedList

class Pattern:
    def __init__(self, pattern, length):
        self.pattern = SortedList(pattern)
        self.length = length

    def __repr__(self):
        return f'Pattern(pattern={self.pattern}, length={self.length})'

    def __eq__(self, other):
        return self.pattern == other.pattern and self.length == other.length

    def __iter__(self):
        return iter(self.pattern)

    def __add__(self, other):
        if not isinstance(other, Pattern):
            raise TypeError(f'Can only add Pattern with Pattern, not {type(other)}.')
        newp = self.pattern + [p + self.length for p in other.pattern]
        newl = self.length + other.length
        return Pattern(newp, newl)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def __iadd__(self, other):
        self.pattern += [p + self.length for p in other.pattern]
        self.length += other.length
        return self

    def __mul__(self, n):
        if not isinstance(n, int):
            raise TypeError('Can only multiply Pattern by int, not {type(other)}.')
        newp = SortedList()
        newl = 0
        for i in range(n):
            newp += [p + newl for p in self.pattern]
            newl += self.length
        return Pattern(newp, newl)

    def __rmul__(self, n):
        return self.__mul__(n)

    def __imul__(self, n):
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
        return len(self.pattern)

    def merge(self, other):
        newp = self.pattern.copy()
        for p in other.pattern:
            if p not in newp:
                newp.add(p)
        newl = max(self.length, other.length)
        return Pattern(newp, newl)

    def on(self, beat):
        return Pattern([(beat-1) + p for p in self.pattern], self.length)

    def onmeasure(self, measure, measurelen=None):
        if measurelen == None:
            measurelen = self.length
        return self.on(beat = 1 + (measure - 1) * measurelen)

    def chop(self, beat):
        newp = [p for p in self.pattern if p < beat]
        newl = beat
        return Pattern(newp, newl)

    def copy(self):
        return Pattern(self.pattern, self.length)

    def until(self, beat):
        repeats, extra = divmod(beat, self.length)
        return self.copy() * repeats + self.copy().chop(extra)

