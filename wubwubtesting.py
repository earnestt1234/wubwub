import wubwub as wb
import wubwub.sounds as snd

import pydub

p1 = '/Users/earnestt1234/Desktop/test.wav'
p2 = '/Users/earnestt1234/Desktop/test2.wav'

a = pydub.AudioSegment.from_file(p1)
b = pydub.AudioSegment.from_file(p2)