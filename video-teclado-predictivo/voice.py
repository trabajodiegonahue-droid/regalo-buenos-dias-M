"""Genera la voz en off con Kokoro (TTS neuronal local) y la línea de tiempo de subtítulos.

Uso: python3 voice.py <carpeta_modelo_kokoro> <carpeta_salida> [voz]
  - carpeta_modelo_kokoro: contiene kokoro-v1.0.onnx y voices-v1.0.bin
    (https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
  - voz: em_alex (hombre, por defecto) o ef_dora (mujer)
Salida: voice.wav y voice-timeline.js (window.VOICE = {...}) que usa la animación.
"""
import json, os, re, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL, OUT = sys.argv[1], sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else 'em_alex'
os.makedirs(OUT, exist_ok=True)

# show = lo que se lee en pantalla; sub = cómo se pronuncia una palabra (mismo número de palabras)
SENTS = [
    dict(id='hook',     show='¡Tu iPhone hace trampa cada vez que escribes!', speed=1.12, gap=.12),
    dict(id='nadie',    show='Y casi nadie lo sabe.', speed=1.08, gap=.30),
    dict(id='iguales',  show='Las teclas se ven todas del mismo tamaño…', gap=.10),
    dict(id='zonas',    show='pero cada una tiene una zona invisible que detecta tu dedo.', gap=.25),
    dict(id='cambia',   show='Y esa zona cambia con cada letra que escribes.', gap=.35),
    dict(id='mira',     show='Mira: si escribes H, O, L…', sub={'H,': 'hache,', 'O,': 'o,', 'L…': 'ele…'}, speed=1.0, gap=.12),
    dict(id='calcula',  show='tu iPhone calcula que la letra más probable es la A.', sub={'A.': 'a.'}, gap=.25),
    dict(id='agranda',  show='Entonces, en secreto, agranda la zona de la A…', sub={'A…': 'a…'}, gap=.15),
    dict(id='achica',   show='y achica las letras que casi nunca irían ahí.', gap=.35),
    dict(id='entre',    show='Así, aunque toques justo entre la A y la S…', sub={'A': 'a', 'S…': 'ese…'}, gap=.12),
    dict(id='hola',     show='se escribe “hola”, y no “hols”.', sub={'“hola”,': 'hola,', '“hols”.': 'hols.'}, gap=.40),
    dict(id='millones', show='Y lo hace con cada letra, comparando millones de palabras…', gap=.10),
    dict(id='tuyas',    show='y las que tú más usas.', gap=.35),
    dict(id='rapido',   show='Por eso puedes escribir rápido, sin mirar, y casi sin errores.', gap=.30),
    dict(id='sugiere',  show='Y arriba te sugiere la palabra completa antes de que la termines.', gap=.40),
    dict(id='mente',    show='Tu teclado prácticamente te lee la mente.', speed=1.02, gap=.35),
    dict(id='comparte', show='Compártelo con alguien que no lo sabía.', gap=1.3),
]
DEFAULT_SPEED = 1.06
LEAD = 0.04            # la voz arranca casi en el cuadro 0 (gancho en el primer segundo)

k = Kokoro(os.path.join(MODEL, 'kokoro-v1.0.onnx'), os.path.join(MODEL, 'voices-v1.0.bin'))
SR = 24000


def trim(a, thr=.012, margin=.03):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    s = max(0, idx[0] - int(margin * SR)); e = min(len(a), idx[-1] + int(margin * SR))
    return a[s:e]


def silent_gaps(a, min_len=.07):
    """Pausas internas (inicio, fin) en segundos."""
    hop = int(.01 * SR)
    rms = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    thr = max(rms.max() * .06, 1e-4)
    quiet = rms < thr
    gaps, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * .01 >= min_len and i > 0 and j < len(quiet):
                gaps.append((i * .01, j * .01))
            i = j
        else:
            i += 1
    return gaps


def weight(w):
    letters = re.sub(r'[^\wáéíóúñü]', '', w.lower())
    return max(1.5, len(letters)) + 1.2


def word_times(show_words, say_words, dur, gaps):
    """Reparte el tiempo entre palabras según su largo y ajusta los cortes de puntuación a las pausas reales."""
    ws = [weight(s) for s in say_words]
    tot = sum(ws)
    # tiempos uniformes por peso
    cum = np.cumsum([0] + ws) / tot * dur
    # puntos de corte donde hay puntuación (después de la palabra i)
    cuts = {}
    for i, w in enumerate(show_words[:-1]):
        if re.search(r'[,…:;.!?]$', w):
            exp = cum[i + 1]
            best = min(gaps, key=lambda g: abs((g[0] + g[1]) / 2 - exp), default=None)
            if best and abs((best[0] + best[1]) / 2 - exp) < .45:
                cuts[i + 1] = best
                gaps = [g for g in gaps if g != best]
    # segmentos entre cortes anclados
    anchors = [(0, 0.0, 0.0)] + sorted((i, g[0], g[1]) for i, g in cuts.items()) + [(len(ws), dur, dur)]
    t0 = [0.0] * len(ws); t1 = [0.0] * len(ws)
    for (ia, _, sa), (ib, eb, _) in zip(anchors, anchors[1:]):
        seg = ws[ia:ib]; st = sa; length = max(.05, eb - sa); sw = sum(seg) or 1
        for j, w in enumerate(seg):
            t0[ia + j] = st; st += length * w / sw; t1[ia + j] = st
    return t0, t1


audio = [np.zeros(int(LEAD * SR), dtype=np.float32)]
t = LEAD
timeline = []
for s in SENTS:
    show_words = s['show'].split()
    sub = s.get('sub', {})
    say_words = [sub.get(w, w) for w in show_words]
    say = ' '.join(say_words).replace('“', '').replace('”', '')
    a, sr = k.create(say, voice=VOICE, speed=s.get('speed', DEFAULT_SPEED), lang='es-419')
    assert sr == SR
    a = trim(a.astype(np.float32))
    dur = len(a) / SR
    t0, t1 = word_times(show_words, say_words, dur, silent_gaps(a))
    timeline.append(dict(id=s['id'], show=s['show'], start=round(t, 3), end=round(t + dur, 3),
                         words=[dict(w=w, t0=round(t + a0, 3), t1=round(t + a1, 3)) for w, a0, a1 in zip(show_words, t0, t1)]))
    print(f"{t:6.2f}-{t + dur:6.2f}  {k.tokenizer.phonemize(say, 'es-419')}")
    audio.append(a)
    gap = np.zeros(int(s['gap'] * SR), dtype=np.float32)
    audio.append(gap)
    t += dur + s['gap']

full = np.concatenate(audio)
full = full / max(1e-6, np.abs(full).max()) * .9
sf.write(os.path.join(OUT, 'voice.wav'), full, SR)
total = round(len(full) / SR, 3)
with open(os.path.join(OUT, 'voice-timeline.js'), 'w') as f:
    f.write('window.VOICE = ' + json.dumps(dict(voice=VOICE, dur=total, sents=timeline), ensure_ascii=False, indent=1) + ';\n')
print('duración total', total, 's')
