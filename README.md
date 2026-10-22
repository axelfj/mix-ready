# Mix Ready

**Check your mix before it goes to mastering.** Mix Ready looks at the file you are
about to send and tells you, in plain words, what to change in your DAW:

- **Headroom**: clipping, overs in float files, peaks above -3 dBFS.
- **Master bus**: a limiter, clipper or maximizer left on (the most common pre-master
  mistake), or a mix that is already as loud as a master.
- **Edges**: audio that starts on the very first sample, or a reverb tail cut at the end.
- **Format**: 16-bit exports, 16-bit audio hiding in a 24-bit file, low sample rates, mono files.
- **Phase**: left and right cancelling, or a wide, out-of-phase low end below 120 Hz that
  disappears in mono and on club systems.
- **DC offset**.

When everything passes it says **Ready for mastering**. Save the HTML report and send
it along with the mix so the engineer sees the numbers too.

Free and open source (MIT), made by [ROMMUSER](https://rommuser.com) for the clients of
[ROMMUSER Studio](https://rommuser.com/estudio) and anyone else sending mixes out. Part
of a set with [Master Check](https://github.com/axelfj/master-check),
[Ref Match](https://github.com/axelfj/ref-match) and
[Stem Organizer](https://github.com/axelfj/stem-organizer).

## Download

Get the latest version from the [Releases page](https://github.com/axelfj/mix-ready/releases/latest):

| System | File |
|---|---|
| Windows 10/11 (64-bit) | `MixReady-Setup.exe` (installer) |
| macOS 12+ on Apple silicon | `MixReady.dmg` (drag *Mix Ready* to Applications) |

The apps are not code-signed yet, so the first launch shows a warning once:

- **Windows**: SmartScreen says "Windows protected your PC". Click *More info*, then *Run anyway*.
- **macOS**: open the app once, then go to *System Settings > Privacy & Security* and
  click *Open Anyway*.

## Using it

Click **Check files...** and pick your mix. You get something like:

```
== My Track - mix v3.wav  [WARN] Fix 2 things before sending.
   WAV, 48000 Hz, 24-bit int, 2 ch, 401.3 s
   Sample peak              -0.3 dBFS
   Peak to loudness (PLR)   7.9 dB
   ...
  WARN  Peaks at -0.3 dBFS: very little headroom.
        Fix: Turn the master fader down so it peaks between -6 and -3 dBFS.
  WARN  Looks limited or clipped on the master bus: 31% of the track hits the same
        ceiling and the peak-to-loudness ratio is 7.9 dB.
        Fix: Bypass any limiter, clipper or maximizer on the master bus before exporting.
```

### Command line

```
python app.py "My Track - mix v3.wav" --html report.html
```

Exit code is 1 when a file has a FAIL.

## How the checks work

| Check | Rule |
|---|---|
| Clipping | 3 or more samples in a row at full scale |
| Headroom | sample peak above -3 dBFS warns; below -10 dBFS is noted as quiet |
| Limiter on the master bus | more than 5 % of 100 ms windows peak within 0.2 dB of the maximum **and** peak-to-loudness ratio under 10 dB. Otherwise, integrated loudness above -11 LUFS warns |
| Cut start | first 10 ms louder than -40 dBFS RMS with no silence before it |
| Cut tail | last 10 ms louder than -50 dBFS RMS |
| Real bit depth | every sample sits on the 16-bit grid |
| Low-end phase | L/R correlation under 0.5 after a 120 Hz low-pass |

The limiter check is a heuristic: a heavily compressed mix without a limiter can trip
it, and a gentle limiter may pass. Loudness follows ITU-R BS.1770-5 and EBU Tech 3342.

## Run from source

```
pip install -r requirements.txt
python app.py
```

Tests: `python -m unittest discover -s tests -v`. See [CONTRIBUTING.md](CONTRIBUTING.md)
and [CHANGELOG.md](CHANGELOG.md).

## En español

**Mix Ready** revisa tu mezcla antes de mandarla a masterizar: clipping, headroom, un
limitador olvidado en el master, inicios o colas cortadas, archivos de 16 bits, fase en
los graves y DC offset. Cada problema viene con lo que tenés que cambiar en tu DAW.
Descargá el instalador de Windows o el .dmg de Mac en
[Releases](https://github.com/axelfj/mix-ready/releases/latest).

¿Lista para masterizar? [ROMMUSER Studio](https://rommuser.com/estudio).

## License

MIT. See [LICENSE](LICENSE).
