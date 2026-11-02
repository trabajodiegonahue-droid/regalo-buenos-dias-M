# Video: cómo funcionan las teclas del iPhone 📱

`teclas-iphone.mp4`: video vertical (1080×1920, 30 fps, unos 2 minutos) con efectos de sonido y música suave.

## Qué explica
1. **Conoce tus botones**: dónde está cada uno.
2. **Botón lateral**: 1 toque (bloquear o encender), mantener (Siri) y 2 toques (Wallet / Apple Pay).
3. **Volumen**: subir y bajar, y tomar fotos con la cámara abierta.
4. **Botón de Acción**: modo silencio y cómo personalizarlo.
5. **Control de la cámara**: abrir la cámara, tomar fotos o grabar video, y deslizar para hacer zoom.
6. **Combinaciones**: captura de pantalla, apagar y forzar reinicio.
7. **Teclado**: mayúsculas, acentos, espacio como trackpad, doble espacio, números y emojis, y borrar rápido.

## Cómo se hizo
- `teclas-iphone.html`: toda la animación. Si lo abres en el navegador, se reproduce en bucle.
- `render.js`: captura cada cuadro con Chromium (Playwright) y lo codifica con ffmpeg.
- `audio.py`: genera los clics, las teclas, el obturador y la música de fondo.
- `build.sh`: corre todo y produce `teclas-iphone.mp4`.

```bash
./build.sh
```
