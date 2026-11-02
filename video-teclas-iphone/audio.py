"""Genera la pista de audio (efectos + música suave) a partir de timeline.json.
Uso: python3 audio.py timeline.json salida.wav
"""
import json, sys, wave
import numpy as np

SR = 44100
tl = json.load(open(sys.argv[1]))
dur = tl['dur'] + 0.5
N = int(SR * dur)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)

def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))

def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y

def tone(f, n, tau, phase=0):
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t + phase) * env_exp(n, tau)

def snd_click():          # botón físico: "clac" corto y grave
    n = int(.06 * SR)
    noise = rng.standard_normal(n) * env_exp(n, .004)
    body = tone(1900, n, .010) * .6 + tone(420, n, .018) * .5
    return (lowpass(noise, .5) * .9 + body) * .55

def snd_release():
    return snd_click() * .45

def snd_tap():            # tecla del teclado: tic seco
    n = int(.035 * SR)
    noise = rng.standard_normal(n) * env_exp(n, .0025)
    return (noise - lowpass(noise, .25)) * .32 + tone(3200, n, .004) * .12

def snd_haptic():         # toque suave (Control de la cámara)
    n = int(.08 * SR)
    return tone(170, n, .02) * .55

def snd_tick():
    n = int(.03 * SR)
    return tone(2600, n, .005) * .25 + (rng.standard_normal(n) * env_exp(n, .002)) * .12

def snd_shutter():        # obturador: dos golpes de ruido filtrado
    n = int(.22 * SR); out = np.zeros(n)
    for off, g in ((0, 1.0), (int(.075 * SR), .75)):
        m = int(.09 * SR)
        b = rng.standard_normal(m) * env_exp(m, .012)
        b = lowpass(b, .35) - lowpass(b, .05)
        out[off:off + m] += b * g
    return out * 1.1

def snd_beep():           # inicio de grabación
    n = int(.16 * SR)
    t = np.arange(n) / SR
    e = np.minimum(1, t / .005) * env_exp(n, .05)
    return np.sin(2 * np.pi * 1320 * t) * e * .18

def snd_whoosh():
    n = int(.55 * SR)
    noise = rng.standard_normal(n)
    sweep = lowpass(noise, .06) * .8 + lowpass(noise, .02) * .6
    t = np.linspace(0, 1, n)
    return sweep * np.sin(np.pi * t) ** 2 * .22

def snd_chime():
    n = int(1.6 * SR); out = np.zeros(n)
    for f, g, d in ((880, .5, 0), (1318.5, .4, .07), (1760, .3, .14)):
        o = int(d * SR); m = n - o
        out[o:] += (tone(f, m, .55) + tone(f * 2.01, m, .2) * .25) * g
    return out * .38

SFX = dict(click=snd_click, release=snd_release, tap=snd_tap, haptic=snd_haptic, tick=snd_tick,
           shutter=snd_shutter, beep=snd_beep, whoosh=snd_whoosh, chime=snd_chime)
PAN = dict(click=.0, tap=.0)

for ev in tl['events']:
    s = SFX[ev['type']]()
    i = int(ev['t'] * SR)
    j = min(N, i + len(s))
    s = s[:j - i]
    L[i:j] += s; R[i:j] += s

# ---- música de fondo: acordes suaves (Cmaj7 - Am7 - Fmaj7 - G6), 4 s cada uno ----
def midi(m): return 440 * 2 ** ((m - 69) / 12)
CHORDS = [[48, 55, 64, 71], [45, 52, 60, 67], [41, 48, 57, 64], [43, 50, 59, 64]]
bar = 4.0
t_all = np.arange(N) / SR
pad = np.zeros(N); padR = np.zeros(N)
k = 0; t0 = 0.0
while t0 < dur:
    ch = CHORDS[k % 4]
    a = int(t0 * SR); n = min(N - a, int((bar + 1.5) * SR))
    if n <= 0: break
    t = np.arange(n) / SR
    e = np.minimum(1, t / 1.2) * np.clip((bar + 1.5 - t) / 1.5, 0, 1)
    for idx, m in enumerate(ch):
        f = midi(m + 12)
        v = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.003 * t + 1) + .15 * np.sin(2 * np.pi * 2 * f * t)) * e
        pan = .35 + .1 * idx
        pad[a:a + n] += v * (1 - pan); padR[a:a + n] += v * pan
    # nota de bajo
    fb = midi(ch[0] - 12)
    vb = np.sin(2 * np.pi * fb * t) * e
    pad[a:a + n] += vb * .6; padR[a:a + n] += vb * .6
    # arpegio suave (campanitas)
    for s_i, m in enumerate([ch[1] + 24, ch[2] + 24, ch[3] + 24, ch[2] + 24]):
        o = int((s_i * 1.0) * SR)
        if a + o >= N: break
        m_n = min(N - a - o, int(1.2 * SR))
        bell = tone(midi(m), m_n, .35) * .5
        pad[a + o:a + o + m_n] += bell * .6; padR[a + o:a + o + m_n] += bell * .4
    k += 1; t0 += bar

trem = 1 + .06 * np.sin(2 * np.pi * .25 * t_all)
music_gain = .11
fade = np.clip(t_all / 1.5, 0, 1) * np.clip((tl['dur'] - t_all) / 1.2, 0, 1)
L += pad * trem * music_gain * fade
R += padR * trem * music_gain * fade

mix = np.stack([L, R], 1)
peak = np.max(np.abs(mix))
mix = mix / peak * 0.89
data = (mix * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(data.tobytes())
print('audio', round(dur, 2), 's  pico original', round(float(peak), 3))
