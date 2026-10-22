import os
import tempfile
import unittest

import numpy as np

from mix_ready import audio, report
from mix_ready.analysis import analyze, ceiling_density
from mix_ready.cli import main as cli_main

RATE = 44100


def mix(seconds=20, peak_db=-6.0, seed=0, fade=True):
    """Noise with a musical envelope, a mono low end and silent edges: a sane pre-master."""
    rng = np.random.default_rng(seed)
    n = int(RATE * seconds)
    t = np.arange(n) / RATE
    env = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.25 * t))
    left, right = rng.normal(0, 1, n), rng.normal(0, 1, n)
    side = 0.6 * (left + right) / 2
    bass = 0.8 * np.sin(2 * np.pi * 55 * t)
    x = np.stack([env * (side + 0.4 * left) + bass, env * (side + 0.4 * right) + bass], 1)
    if fade:
        ramp = np.minimum(1.0, np.minimum(t, t[-1] - t) / 1.0)
        x *= ramp[:, None]
        x[: RATE // 2] = 0
        x[-RATE:] = 0
    return x / np.max(np.abs(x)) * 10 ** (peak_db / 20)


def messages(r):
    return " | ".join(f["message"] for f in r["findings"])


class MixReadyTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def write(self, x, name="mix.wav", bits=24):
        p = os.path.join(self.dir, name)
        audio.write_wav_pcm(p, x, RATE, bits)
        return p

    def test_clean_mix_is_ready(self):
        r = analyze(self.write(mix()))
        self.assertTrue(r["ready"], messages(r))
        self.assertIn("Ready for mastering", report.text([r]))

    def test_limited_mix_is_flagged(self):
        x = mix(peak_db=0) * 4
        x = np.clip(x, -0.9, 0.9)            # brick-wall at -0.9 dBFS
        r = analyze(self.write(x))
        self.assertIn("limited", messages(r))
        self.assertFalse(r["ready"])

    def test_ceiling_density_separates_limited_from_dynamic(self):
        dyn = mix()
        self.assertLess(ceiling_density(dyn, RATE), 0.05)
        lim = np.clip(dyn * 8, -0.5, 0.5)
        self.assertGreater(ceiling_density(lim, RATE), 0.5)

    def test_no_headroom_and_clipping(self):
        r = analyze(self.write(mix(peak_db=-1)))
        self.assertIn("little headroom", messages(r))
        x = mix(peak_db=0)
        x[5 * RATE:5 * RATE + 20] = 1.0
        r = analyze(self.write(x, "clip.wav"))
        self.assertEqual(r["status"], "fail")

    def test_float_overs(self):
        p = os.path.join(self.dir, "f.wav")
        audio.write_wav_float(p, mix(peak_db=3), RATE)
        self.assertIn("above 0 dBFS", messages(analyze(p)))

    def test_cut_start_and_tail(self):
        r = analyze(self.write(mix(fade=False)))
        self.assertIn("first sample", messages(r))
        self.assertIn("tail is cut", messages(r))

    def test_16_bit_and_padded(self):
        self.assertIn("16-bit file", messages(analyze(self.write(mix(), "a.wav", bits=16))))
        padded = np.round(mix() * 32768) / 32768
        self.assertIn("really 16-bit", messages(analyze(self.write(padded, "b.wav"))))

    def test_wide_low_end(self):
        x = mix()
        t = np.arange(len(x)) / RATE
        x[:, 1] -= 2 * 0.3 * np.sin(2 * np.pi * 55 * t) * (np.abs(x[:, 1]) > 0)
        x = x / np.max(np.abs(x)) * 0.5
        r = analyze(self.write(x))
        self.assertIn("Low end", messages(r))

    def test_cli_and_reports(self):
        self.write(mix(), "good.wav")
        out = os.path.join(self.dir, "r.html")
        self.assertEqual(cli_main([self.dir, "--html", out]), 0)
        with open(out, encoding="utf-8") as f:
            page = f.read()
        self.assertIn("Ready for mastering", page)
        self.assertIn("rommuser.com/estudio", page)


if __name__ == "__main__":
    unittest.main()
