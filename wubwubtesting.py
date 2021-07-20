from pysndfx import AudioEffectsChain
import wubwub as wb
import wubwub.sounds as snd

ORGAN = snd.load('keys.organ')
DRUMS = snd.load('drums.house')
DRUMS2 = snd.load('drums.ukhard')
FX = snd.load('synth.fx')
SYNTH = snd.load('synth.ts_synth')

end = 40
seq = wb.Sequencer(bpm=400, beats=40)

emph = wb.Pattern([1, 4, 7, 9], length=10)
notemph = wb.Pattern([2, 3, 5, 6, 8, 10], length=10)
every = emph.merge(notemph)
kickpat = wb.Pattern([1, 4, 6], length=10)
snarepat = wb.Pattern([7, 10], length=10)
phase = wb.Pattern([1], length=4)
bleeppat = wb.Pattern([1,2,], length=4)
synthpat = wb.Pattern([1, 4, 6, 7], length=10)

organ = seq.add_sampler(ORGAN['C1'], name='organ', basepitch='C1')
organ.make_notes(every.until(end), pitches=[3,2,0,5,3,2,7,3,5,2])

hat = seq.add_sampler(DRUMS['hat1'], name='hat')
hat.make_notes(emph.until(end), volumes=0)
hat.make_notes(notemph.until(end), volumes=-5, lengths=.1)
hat.volume -= 10
hat.pan = .5

snare = seq.add_sampler(DRUMS['snare3'], name='snare')
snare.make_notes(snarepat.until(end), volumes=[0, -5])

kick = seq.add_sampler(DRUMS['kick6'], name='kick')
kick.make_notes(kickpat.until(end))
kick.volume -= 2
organ[kick.array_of_beats()] = wb.alter_notes(organ[kick.array_of_beats()], volume=-5)

ride = seq.add_sampler(DRUMS2['ride-hard'], name='ride')
ride.make_notes(phase.until(end), lengths=5)
ride.pan = -.6
ride.effects = AudioEffectsChain().highpass(5000)

bleep = seq.add_sampler(wb.shift_pitch(FX['checkpoint-hit'], 8), name='bleep')
bleep.make_notes(bleeppat.until(end))
bleep.effects = AudioEffectsChain().reverb(wet_gain=5)

synth = seq.add_sampler(SYNTH['patch001'], name='synth')
synth.make_notes(every.until(end), pitches=[12,12,12,0,0,0,12,12,0,0], lengths=.2)
synth.effects = AudioEffectsChain().reverb()

intro = seq.copy(with_notes=False)
intro['organ'].add_fromdict(seq['organ'].notedict)
intro['organ'].effects = AudioEffectsChain().lowpass(400)

final = wb.join([intro, seq])
final.build(overhang=5)