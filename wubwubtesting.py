import os

import pydub

path = '/Users/earnestt1234/Desktop/SAMPLES'

for root, folders, files in os.walk(path):
    for file in files:
        if not file.endswith('wav'): continue;
        full = os.path.join(root, file)
        print(file)
        snd = pydub.AudioSegment.from_file(full)
        print(snd.frame_rate, snd.sample_width)