from pysndfx import AudioEffectsChain
import wubwub as wb
import wubwub.sounds as snd

GUITAR = snd.load('guitar.acoustic')
DRUMS = snd.load('drums.606')
DRUMS2 = snd.load('drums.esoul')
BASS = snd.load('bass.acoustic')
RHODES = snd.load('keys.rhodes')

seq = wb.Sequencer(bpm=60, beats=8)
guitar = seq.add_multisampler(name='guitar', overlap=False)
guitar.add_sample('ii', GUITAR['Emin7'])
guitar.add_sample('V', GUITAR['A702'])
guitar.add_sample('I', GUITAR['Dmaj'])
guitar.make_notes(beats=[1,3,5], pitches=['ii', 'V', 'I'], lengths=4)
guitar.effects = AudioEffectsChain().bandpass(400).tremolo(2)
guitar.pan = -.75

kick = seq.add_sampler(name='kick', sample=DRUMS['kick1'])
kick.make_notes(beats=[1, 2.5, 3, 5, 6.5, 7])
kick.effects = AudioEffectsChain().lowpass(200)
kick.volume -= 5

snare = seq.add_sampler(name='snare', sample=DRUMS['snare2'])
snare.make_notes(beats=[2, 4, 6, 8])
snare.effects = AudioEffectsChain().lowpass(2000).highpass(400)

hat = seq.add_sampler(name='hat', sample=DRUMS2['hhclonec'])
hat.make_notes_every(freq=.5)
hat.effects = AudioEffectsChain().lowpass(1000)

bass = seq.add_sampler(name='bass', sample=BASS['E2'], basepitch='E2')
bass.make_notes_every(freq=1, pitches=['E2', 'B2', 'A2', 'C#2', 'D2', 'D3', 'C3', 'F#2'])
bass.effects = AudioEffectsChain().lowpass(200).highpass(100)

rhodes = seq.add_sampler(name='rhodes', sample=RHODES['A3'], basepitch='A3')
rhodes.make_notes(beats=[1.5, 1.75, 2, 2.5, 3, 3.5, 4, 4.5, 5],
                  pitches=['F#3', 'E3', 'F#3', 'E3', 'B3', 'A3', 'E3', 'A3', 'F#3'])
rhodes.effects = AudioEffectsChain().lowpass(300).highpass(100).reverb(100).tremolo(3)
rhodes.volume -= 5

rhodes2 = seq.duplicate_track('rhodes', newname='rhodes2', with_notes=False)
rhodes2.effects = AudioEffectsChain().lowpass(400).highpass(100)
e = wb.chord_from_name('E3', 'm7', lengths=.25)
a = wb.chord_from_name('A3', '7', lengths=.25)
d = wb.chord_from_name('D3', 'M7', lengths=.25)
d7 = wb.chord_from_name('D3', '7', lengths=.25)
rhodes2[[1, 1.5, 2, 2.5]] = e
rhodes2[[3, 3.5, 4, 4.5]] = a
rhodes2[[5, 5.5, 6, 6.5]] = d
rhodes2[[7, 7.5, 8, 8.5]] = d7
rhodes2.volume -= 10
rhodes2.pan = .75

seq.volume += 3
seq.loop(2, internal_overhang=2, end_overhang=4)