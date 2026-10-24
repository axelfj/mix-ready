# Changelog

## Unreleased: V2 preparation

- Rechazar audio vacío/no finito; silencio devuelve fail y ready=false; JSON estricto y regresiones en CI.
- Todavía no constituye una versión V2 publicada ni valida binarios nativos.

All notable changes to Mix Ready are listed here. Versions follow
[Semantic Versioning](https://semver.org).

## [0.1.0] - 2026-10-22

First release.

- Checks a pre-master for: clipping, overs in float files, headroom outside -10 to -3 dBFS,
  a limiter or clipper left on the master bus, very loud pre-masters, audio cut at the
  start or at the end, 16-bit exports and 16-bit audio padded to 24-bit, low sample rates,
  mono files, phase problems overall and below 120 Hz, DC offset.
- Every problem comes with the fix to make in the DAW.
- Loudness, true peak and LRA per ITU-R BS.1770-5 and EBU Tech 3342.
- Reads WAV (including RF64 and 32-bit float), AIFF, FLAC, MP3 and OGG.
- Window app plus command line, with HTML and JSON reports to send along with the mix.
- Windows installer and macOS (Apple silicon) disk image.

