import wubwub as wb
import wubwub.sounds as snd

import pydub

a = wb.Note()
b = wb.Note(pitch='A3', length=2, volume=1)
c = a + b

arp = wb.ArpChord([a,b], length=1)