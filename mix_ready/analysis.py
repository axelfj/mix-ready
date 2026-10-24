"""
Checks one pre-master (a mix bounced for mastering) and explains each problem
in plain words, with what to change in the DAW.
"""
import math

import numpy as np
from scipy import signal

from . import audio, loudness, stats

FAIL, WARN, OK, INFO = "fail", "warn", "ok", "info"
SEVERITY = {FAIL: 3, WARN: 2, INFO: 1, OK: 0}

PEAK_HIGH = -3.0       # dBFS: less headroom than this leaves the engineer nothing to work with
PEAK_LOW = -10.0       # dBFS: quieter than this is fine but unusual
LOW_END_HZ = 120.0
CEILING_DB = 0.2       # windows peaking this close to the maximum count as "at the ceiling"
WINDOW_S = 0.1


def finding(level, message, fix=""):
    return {"level": level, "message": message, "fix": fix}


def worst(findings):
    top = max([f["level"] for f in findings] or [OK], key=SEVERITY.get)
    return OK if top == INFO else top


def ceiling_density(samples, rate, window_s=WINDOW_S, within_db=CEILING_DB):
    """
    Share of short windows whose peak sits within within_db of the file's peak.
    A limiter or clipper on the master bus pins many windows to one ceiling;
    an unlimited mix only touches its maximum a few times.
    """
    peaks = np.max(np.abs(samples), axis=1)
    win = max(1, int(rate * window_s))
    n = len(peaks) // win
    if n == 0:
        return 0.0
    per_window = peaks[: n * win].reshape(n, win).max(axis=1)
    top = per_window.max()
    if top <= 0:
        return 0.0
    loud = per_window > top * 10 ** (-20 / 20)  # ignore silent intro/outro windows
    if not loud.any():
        return 0.0
    hits = per_window >= top * 10 ** (-within_db / 20)
    return float(np.count_nonzero(hits & loud)) / float(np.count_nonzero(loud))


def low_end_correlation(samples, rate, cutoff=LOW_END_HZ):
    if samples.shape[1] != 2:
        return None
    sos = signal.butter(4, cutoff, "lowpass", fs=rate, output="sos")
    low = signal.sosfilt(sos, samples.astype(np.float64), axis=0)
    if np.max(np.abs(low)) < 1e-4:  # no low end to speak of
        return None
    return stats.correlation(low[:, 0], low[:, 1])


def measure_file(path):
    a = audio.read(path)
    x = a.samples
    m = loudness.measure(x, a.rate)
    head, tail = stats.edge_silence(x, a.rate)
    head_rms, tail_rms = stats.edge_rms_db(x, a.rate)
    m.update({
        "clip_runs": stats.clip_runs(x),
        "overs": stats.overs(x),
        "dc_offset_dbfs": stats.dc_offset_db(x),
        "correlation": stats.correlation(x[:, 0], x[:, 1]) if a.channels == 2 else None,
        "low_end_correlation": low_end_correlation(x, a.rate),
        "dual_mono": stats.is_dual_mono(x),
        "head_silence_s": head,
        "tail_silence_s": tail,
        "head_rms_dbfs": head_rms,
        "tail_rms_dbfs": tail_rms,
        "ceiling_density": ceiling_density(x, a.rate),
        "effective_bits": stats.effective_bits(x, a.bits, a.is_float),
    })
    fmt = {"container": a.container, "encoding": a.encoding, "rate": a.rate, "bits": a.bits,
           "float": a.is_float, "channels": a.channels, "duration_s": a.duration,
           "description": a.describe()}
    return fmt, m


def check(fmt, m):
    out = []
    peak, tp, i, plr = (m["sample_peak_dbfs"], m["true_peak_dbtp"], m["integrated_lufs"],
                        m["plr_db"])

    # Silence is not a valid pre-master. A short non-silent file may have
    # unmeasurable LUFS, so distinguish it using sample peak.
    if peak == loudness.NEG_INF:
        out.append(finding(FAIL, "The file is silent.", "Export a bounce containing the mix audio."))
    elif not math.isfinite(i):
        out.append(finding(WARN, "Not enough measurable audio for integrated loudness.",
                           "Export a longer passage or the full track."))

    # File format
    if fmt["rate"] < 44100:
        out.append(finding(FAIL, "Sample rate is %d Hz." % fmt["rate"],
                           "Export at your session's rate (44.1 kHz or higher)."))
    if not fmt["float"] and fmt["bits"] < 24:
        out.append(finding(WARN, "%d-bit file." % fmt["bits"],
                           "Export 24-bit or 32-bit float so no detail is lost before mastering."))
    elif not fmt["float"] and 0 < m["effective_bits"] < fmt["bits"]:
        out.append(finding(WARN, "Saved as %d-bit but the audio is really %d-bit."
                           % (fmt["bits"], m["effective_bits"]),
                           "Export straight from the session at 24-bit or 32-bit float, "
                           "not from a 16-bit bounce."))
    if fmt["channels"] == 1:
        out.append(finding(WARN, "Mono file.", "Export the stereo mix."))
    if fmt["duration_s"] < 10.0:
        out.append(finding(WARN, "Only %.1f seconds long." % fmt["duration_s"],
                           "Export the full track from the very start to the end of the tail."))

    # Level and headroom
    if m["clip_runs"]:
        out.append(finding(FAIL, "Clipped in %d places." % m["clip_runs"],
                           "Turn the master fader down until the loudest part peaks around "
                           "-6 dBFS and export again. Clipping can't be undone in mastering."))
    elif m["overs"]:
        out.append(finding(WARN, "Peaks above 0 dBFS (%+.1f dBFS). The float file keeps them, "
                                 "but they clip on any conversion." % peak,
                           "Turn the master fader down so it peaks around -6 dBFS."))
    elif peak > PEAK_HIGH:
        out.append(finding(WARN, "Peaks at %+.1f dBFS: very little headroom." % peak,
                           "Turn the master fader down so it peaks between -6 and -3 dBFS."))
    elif peak < PEAK_LOW and peak != loudness.NEG_INF:
        out.append(finding(INFO, "Peaks at %+.1f dBFS, on the quiet side." % peak,
                           "Fine for mastering. Around -6 dBFS is ideal."))

    # Master bus processing
    limited = m["ceiling_density"] > 0.05 and plr < 10.0
    if limited:
        out.append(finding(WARN, "Looks limited or clipped on the master bus: %.0f%% of the "
                                 "track hits the same ceiling and the peak-to-loudness ratio is "
                                 "%.1f dB." % (100 * m["ceiling_density"], plr),
                           "Bypass any limiter, clipper or maximizer on the master bus before "
                           "exporting. Keep it on a separate reference bounce if you like the "
                           "sound."))
    elif i > -11.0:
        out.append(finding(WARN, "Very loud for a pre-master (%.1f LUFS)." % i,
                           "If a limiter is on the master bus, bypass it. Mastering needs room "
                           "to work."))

    # Start and end
    if m["head_rms_dbfs"] > -40.0 and m["head_silence_s"] < 0.005:
        out.append(finding(WARN, "Audio starts on the very first sample.",
                           "Start the export a bar earlier so the first transient isn't cut."))
    if m["tail_rms_dbfs"] > -50.0:
        out.append(finding(WARN, "Still sounding on the last sample: the tail is cut.",
                           "Extend the export a few seconds past the end so reverbs and "
                           "delays fade out."))

    # Stereo and phase
    if m["dual_mono"]:
        out.append(finding(INFO, "Left and right are identical (mono in a stereo file).", ""))
    elif m["correlation"] is not None and m["correlation"] < 0.0:
        out.append(finding(WARN, "Left and right are out of phase (correlation %.2f)."
                           % m["correlation"],
                           "Check for a flipped polarity or an extreme stereo widener."))
    lc = m["low_end_correlation"]
    if lc is not None and lc < 0.5 and not m["dual_mono"]:
        out.append(finding(WARN, "Low end below %d Hz is wide or out of phase (correlation "
                                 "%.2f). It loses weight in mono and on club systems."
                           % (LOW_END_HZ, lc),
                           "Keep kick and bass mono below about 120 Hz."))
    if m["dc_offset_dbfs"] > -40.0:
        out.append(finding(WARN, "DC offset of %.0f dBFS." % m["dc_offset_dbfs"],
                           "Find the track causing it (often a sample or a saturator) and add "
                           "a high-pass or DC filter."))
    return out


def analyze(path):
    fmt, m = measure_file(path)
    findings = check(fmt, m)
    status = worst(findings)
    return {"file": path, "format": fmt, "measurements": _clean(m), "findings": findings,
            "status": status, "ready": status == OK}


def _clean(m):
    return {k: (None if isinstance(v, float) and not math.isfinite(v) else v) for k, v in m.items()}

