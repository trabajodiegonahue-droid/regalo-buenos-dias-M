"""Genera la voz en off con Kokoro (TTS neuronal local) y la línea de tiempo de subtítulos.

Uso: python3 voice.py <carpeta_modelo_kokoro> <carpeta_salida> [voz]
  - carpeta_modelo_kokoro: contiene kokoro-v1.0.onnx y voices-v1.0.bin
    (https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0)
  - voz: por defecto 'em_alex:0.7,am_onyx:0.3' (hombre, grave); también em_alex o ef_dora
Salida: voice.wav y voice-timeline.js (window.VOICE = {...}) que usa la animación.
"""
import json, os, re, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

MODEL, OUT = sys.argv[1], sys.argv[2]
VOICE = sys.argv[3] if len(sys.argv) > 3 else 'em_alex:0.7,am_onyx:0.3'
os.makedirs(OUT, exist_ok=True)

# show = lo que se lee en pantalla; sub = cómo se pronuncia una palabra (para que se entienda bien)
LA = {'A': 'letra a', 'A,': 'letra a,', 'A.': 'letra a.', 'A…': 'letra a…', 'A»': 'letra a', 'S.': 'letra ese.', 'S…': 'letra ese…'}
SENTS = [
    dict(id='hook',      show='¡Tu iPhone sabe qué letra vas a tocar… antes que tú!', speed=1.1, gap=.25),
    dict(id='ven',       show='Ven, vamos a meternos adentro para ver cómo lo hace.', gap=.35),
    dict(id='boton',     show='Mira: cuando tocas la pantalla, no estás apretando un botón de verdad.', gap=.15),
    dict(id='vidrio',    show='Es solo vidrio.', speed=.95, gap=.35),
    dict(id='telarana',  show='Pero debajo del vidrio hay una telaraña invisible de rayitas que siente tu dedo.', gap=.25),
    dict(id='avisa',     show='Y cuando la tocas, le avisa al cerebrito del iPhone: ¡aquí tocaron!', gap=.45),
    dict(id='magia',     show='Ahora viene la parte mágica.', speed=.98, gap=.35),
    dict(id='jardin',    show='Imagina que cada tecla es una casita con un jardín invisible alrededor.', gap=.25),
    dict(id='tocar',     show='Si tu dedo cae en el jardín de la A, el iPhone escribe una A.', sub=LA, gap=.35),
    dict(id='hol',       show='Ahora escribe la H, la O y la L…', sub={'H,': 'hache,', 'O': 'o,', 'L…': 'ele.'}, speed=.95, gap=.25),
    dict(id='piensa',    show='El cerebrito piensa: ¡ya sé, quiere escribir “hola”!', gap=.25),
    dict(id='sigue',     show='Lo que sigue tiene que ser la A.', sub=LA, gap=.3),
    dict(id='grande',    show='Entonces, sin que lo veas, le agranda el jardín a la A…', sub=LA, gap=.15),
    dict(id='chico',     show='y se lo achica a las letras que no van, como la S.', sub=LA, gap=.35),
    dict(id='chueco',    show='Así, aunque tu dedo caiga medio torcido, justo en medio de la A y la S…', sub={**LA, 'A': 'letra a,'}, gap=.15),
    dict(id='hola',      show='el iPhone escribe “hola”, y no “hols”.', gap=.45),
    dict(id='aprende',   show='¿Y cómo sabe qué letra sigue? Porque aprendió leyendo muchísimas palabras…', gap=.15),
    dict(id='tuyas',     show='y también aprende las que tú escribes.', gap=.35),
    dict(id='equivocas', show='Por eso casi nunca te equivocas, aunque escribas rápido.', gap=.4),
    dict(id='cierre',    show='Tu teclado no solo espera a que lo toques… ¡te ayuda a darle a la tecla correcta!', gap=.4),
    dict(id='comparte',  show='Compártelo con alguien que no lo sabía.', gap=1.4),
]
DEFAULT_SPEED = 1.05
LEAD = 0.04            # la voz arranca casi en el cuadro 0 (gancho en el primer segundo)

k = Kokoro(os.path.join(MODEL, 'kokoro-v1.0.onnx'), os.path.join(MODEL, 'voices-v1.0.bin'))
SR = 24000
if ':' in VOICE:  # mezcla de voces: más grave y adulta (Kokoro permite promediar estilos)
    STYLE = sum(k.get_voice_style(n) * float(w) for n, w in (x.split(':') for x in VOICE.split(',')))
else:
    STYLE = VOICE


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
    a, sr = k.create(say, voice=STYLE, speed=s.get('speed', DEFAULT_SPEED), lang='es-419')
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
