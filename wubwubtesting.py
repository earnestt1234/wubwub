from pysndfx import AudioEffectsChain
import wubwub as wb
import wubwub.sounds as snd

GUITAR = snd.load('guitar.acoustic')
DRUMS = snd.load('drums.606')
DRUMS2 = snd.load('drums.esoul')
BASS = snd.load('bass.acoustic')
RHODES = snd.load('keys.rhodes')

seq = wb.Sequencer(bpm=60, beats=8)
a = seq.add_sampler(name='a', sample=DRUMS['kick1'])