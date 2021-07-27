import wubwub as wb
import wubwub.sounds as snd

seq = wb.Sequencer(bpm=120, beats=8)

DRUMS = snd.load('drums.808')

kick = seq.add_sampler(sample=DRUMS['kick1'], name='kick')
snare = seq.add_sampler(sample=DRUMS['snare'], name='snare')
seq.duplicate_track('snare', newname='snare2')