from pysndfx import AudioEffectsChain
import wubwub as wb
import wubwub.sounds as snd

synthbass = snd.load('bass.synth')
drums = snd.load('drums.808')
ts = snd.load('synth.ts_synth')

seq = wb.Sequencer(bpm=160, beats=16)

bass = seq.add_sampler(wb.shift_pitch(synthbass['pluck'], 7), name='bass')
bass.make_notes_every(freq=.5, pitches=[0] * 7 + [-4] * 9, volumes = [0, -2])
bass.volume -= 2.5
bass.effects = AudioEffectsChain().lowpass(200)

kick = seq.add_sampler(drums['kick1'], name='kick')
kick.make_notes_every(2)
kick.volume = 5

hat = seq.add_sampler(drums['closed_hihat'], name='closed')
hat.make_notes_every(.5)
hat.volume = -10
hat.pan = -.5

openhat = seq.add_sampler(drums['open_hihat'], name='open')
openhat.make_notes_every(2, 1)
openhat.volume = -20
openhat.pan = +.5

clap = seq.add_sampler(drums['handclap'], name='clap')
clap.make_notes_every(4, offset=2)

arp = seq.add_arpeggiator(wb.shift_pitch(ts['patch007'], -2), name='arp', method='updown')
arp.make_chord(1, pitches=[0, 3, 7, 12, 15, 19, 24, 27, 31], length=16)
arp.volume = -10
arp.effects = AudioEffectsChain().highpass(200)

hi1 = seq.add_sampler(wb.shift_pitch(ts['patch011'], 10), name='hinote1')
hi1.effects = AudioEffectsChain().lowpass(1000).reverb(100 ,wet_gain=10)
hi1.make_notes_every(2, offset=1.5, pitches=[10, 5, 3, 7, 2, 3, 8, 7], lengths=.5)
hi1.pan = .75
hi1.volume = -7

hi2 = seq.add_sampler(wb.shift_pitch(ts['patch011'], 10), name='hinote2')
hi2.effects = AudioEffectsChain().lowpass(1000).reverb(100, wet_gain=10)
hi2.make_notes_every(2, offset=1.5, pitches=[14, 15, 7, 10, 5, 0, 5, 8], lengths=.5)
hi2.pan = -.75
hi2.volume = -7

seq.build(overhang=8)