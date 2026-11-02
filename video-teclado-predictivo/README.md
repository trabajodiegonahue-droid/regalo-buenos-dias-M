# Video: "Tu iPhone hace trampa cada vez que escribes" ⌨️

`teclado-predictivo.mp4`: video vertical (1080×1920, 30 fps, 48 segundos) con **voz en off** y subtítulos sincronizados. **No tiene música**, solo efectos sutiles: teclas, un "pop" y un "ding".

## De qué trata
El teclado del iPhone predice la letra más probable que vas a escribir y, sin que se vea, **agranda la zona táctil invisible** de esa tecla. Al mismo tiempo achica las zonas de las letras improbables. Por ejemplo, después de "Hol" la A crece: si tocas justo entre la A y la S, se escribe "Hola" y no "Hols".

Estructura:
1. **Gancho (segundo 0):** "¡Tu iPhone hace trampa cada vez que escribes!"
2. Las teclas se ven iguales, pero cada una tiene una zona invisible que cambia.
3. Ejemplo H‑O‑L → la A crece y sus vecinas se achican → "Hola" en vez de "Hols".
4. Compara con millones de palabras y con las que tú más usas.
5. Escribir rápido sin mirar, y las sugerencias de palabras arriba del teclado.
6. Cierre: "Tu teclado prácticamente te lee la mente. Compártelo con alguien que no lo sabía."

## Cómo se hizo
- `voice.py`: genera la voz con [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), un TTS neuronal local con licencia Apache‑2.0, en español latinoamericano. También calcula el tiempo de cada palabra para los subtítulos (`voice-timeline.js`).
  - Voz por defecto: `em_alex` (hombre). Para usar una voz de mujer, cambia a `ef_dora`.
- `teclado-predictivo.html`: la animación. Si la abres en el navegador, se reproduce en bucle.
- `render.js`: captura cada cuadro con Chromium (Playwright) y lo codifica con ffmpeg.
- `sfx.py`: genera los efectos de sonido.
- `build.sh`: corre todo. Necesita los archivos `kokoro-v1.0.onnx` y `voices-v1.0.bin` de la [release del modelo](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0).

```bash
./build.sh /ruta/al/modelo-kokoro em_alex
```
