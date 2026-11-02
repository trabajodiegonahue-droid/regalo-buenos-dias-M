"""Efectos de sonido sutiles (sin música) a partir de timeline.json.
Uso: python3 sfx.py timeline.json sfx.wav
"""
import json, sys, wave
import numpy as np

SR = 44100
tl = json.load(open(sys.argv[1]))
N = int(SR * (tl['dur'] + .5))
mix = np.zeros(N)
rng = np.random.default_rng(3)


def env(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y


def tone(f, n, tau):
    return np.sin(2 * np.pi * f * np.arange(n) / SR) * env(n, tau)


def tap():       # clic del teclado del iPhone
    n = int(.035 * SR); nz = rng.standard_normal(n) * env(n, .0025)
    return (nz - lowpass(nz, .25)) * .35 + tone(3200, n, .004) * .12


def pop():       # "pop" cuando algo aparece o crece
    n = int(.14 * SR); t = np.arange(n) / SR
    f = 380 + 900 * np.exp(-t / .03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .045) * .45


def ding():      # correcto
    n = int(.9 * SR)
    return (tone(1046.5, n, .25) * .5 + tone(1568, n, .18) * .3 + tone(2093, n, .1) * .15) * .55


def nope():      # incorrecto (suave)
    n = int(.22 * SR); t = np.arange(n) / SR
    return (np.sign(np.sin(2 * np.pi * 160 * t)) * .25 + np.sin(2 * np.pi * 120 * t) * .5) * env(n, .07) * .22


SFX = dict(tap=tap, pop=pop, ding=ding, nope=nope)
for ev in tl['events']:
    s = SFX[ev['type']](); i = int(ev['t'] * SR); j = min(N, i + len(s))
    mix[i:j] += s[:j - i]

data = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(data.tobytes())
print('sfx', len(tl['events']), 'eventos')
