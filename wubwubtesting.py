import wubwub as wb
import wubwub.sounds as snd

BASS = snd.load('bass.synth')

seq = wb.Sequencer(bpm=120, beats=8)

bass = seq.add_sampler(BASS['pluck'], name='bass')