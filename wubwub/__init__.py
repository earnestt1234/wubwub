# -*- coding: utf-8 -*-
'''wubwub is a novelty music production package for Python.'''

# load the version (and remove from namespace)
from ._version import v
__version__ = v
del v

# imports
from .audio import *
from .errors import *
from .notes import *
from .pattern import *
from .pitch import *
from .plots import *
from .resources import *
from .seqstring import *
from .sequencer import *
from .tracks import *