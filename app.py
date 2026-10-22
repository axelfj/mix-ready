"""
Entry point for the packaged app and for running from source.

  python app.py              opens the window
  python app.py FILE...      command line report (see --help)
  python app.py --selftest   checks a packaged build without opening a window
"""
import sys


def selftest():
    import os
    import tempfile

    import numpy as np
    import tkinter  # noqa: F401  (the window needs it in the bundle)

    from mix_ready import audio, report
    from mix_ready.analysis import analyze

    rate = 48000
    t = np.arange(rate * 5) / rate
    tone = 10 ** (-23 / 20) * np.sin(2 * np.pi * 1000 * t)
    folder = tempfile.mkdtemp()
    wav = os.path.join(folder, "selftest.wav")
    audio.write_wav_pcm(wav, np.stack([tone, tone], 1), rate, 24)
    r = analyze(wav)
    assert abs(r["measurements"]["integrated_lufs"] + 23.0) < 0.1, r["measurements"]
    report.to_html([r])
    import soundfile
    flac = os.path.join(folder, "selftest.flac")
    soundfile.write(flac, np.stack([tone, tone], 1), rate, subtype="PCM_24")
    assert abs(analyze(flac)["measurements"]["integrated_lufs"] + 23.0) < 0.1
    print("selftest OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith("-psn_")]  # old macOS Finder arg
    if args:
        from mix_ready.cli import main as cli_main
        return cli_main(args)
    from mix_ready.gui import main as gui_main
    gui_main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
