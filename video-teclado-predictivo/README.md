# Video: "Tu iPhone sabe qué letra vas a tocar… antes que tú" ⌨️

`teclado-predictivo.mp4`: video vertical (1080×1920, 30 fps, 74 segundos).
- **Imagen:** fondo negro, con el iPhone como protagonista.
- **Voz:** masculina y grave, que explica todo como para un niño de 5 años.
- **Texto:** subtítulos sincronizados palabra por palabra.
- **Sonido:** no tiene música, solo efectos sutiles.

## Guion (resumen)
1. **Gancho (segundo 0):** "¡Tu iPhone sabe qué letra vas a tocar… antes que tú!"
2. **Nos metemos adentro del iPhone:** la cámara entra y el teléfono se abre en capas.
   - **Vidrio:** cuando tocas, no aprietas un botón de verdad.
   - **Telaraña que siente:** se encienden la fila y la columna justo donde tocaste.
   - **Cerebrito (el chip):** recibe el aviso "¡aquí tocaron!".
3. **La parte mágica:** cada tecla es una casita con un **jardín invisible** alrededor. Si tu dedo cae en ese jardín, se escribe esa letra.
4. **El truco:** con "H, O, L" el cerebrito adivina "hola". Entonces agranda el jardín de la A y achica el de las letras que no van, como la S. Así, aunque el dedo caiga entre la A y la S, se escribe "Hola" y no "Hols".
5. **Cómo aprende:** leyendo muchísimas palabras y también las que tú escribes. Por eso casi nunca te equivocas.
6. **Cierre:** "¡Te ayuda a darle a la tecla correcta!" y "Compártelo".

## Cómo se hizo
- **`voice.py`:** genera la voz con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), un TTS neuronal local con licencia Apache‑2.0, en español latinoamericano.
  - La voz por defecto mezcla dos estilos, `em_alex:0.7,am_onyx:0.3`, para que suene más grave y adulta.
  - Algunas palabras se escriben de otra forma para que se pronuncien claras. Por ejemplo, "la A" se dice "la letra a".
  - También calcula el tiempo de cada palabra para los subtítulos (`voice-timeline.js`).
- **Revisión de la voz:** cada frase se transcribió con Whisper (reconocimiento de voz) para confirmar que se entiende bien.
- **`teclado-predictivo.html`:** la animación, con la vista en capas hecha con CSS 3D. Si la abres en el navegador, se reproduce en bucle.
- **`render.js`:** captura cada cuadro con Chromium (Playwright) y lo codifica con ffmpeg.
- **`sfx.py`:** genera los efectos (teclas, pop, ding, whoosh y la señal eléctrica).
- **`build.sh`:** corre todo. Necesita los archivos `kokoro-v1.0.onnx` y `voices-v1.0.bin` de la [release del modelo](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0).

```bash
./build.sh /ruta/al/modelo-kokoro
```
