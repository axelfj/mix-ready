"""Malformed float audio must never become an analysis verdict."""
import json
import numpy as np
import pytest
from mix_ready import audio, report

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("whole_file", [False, True])
def test_reject_nonfinite_audio(tmp_path, bad, whole_file):
    x = np.full((4410, 2), 0.01, dtype=np.float32)
    if whole_file:
        x[:] = bad
    else:
        x[200, 1] = bad
    path = str(tmp_path / "corrupt.wav")
    audio.write_wav_float(path, x, 44100)
    with pytest.raises(audio.AudioError, match="non-finite"):
        audio.read(path)

def test_json_refuses_nonfinite_measurements():
    with pytest.raises(ValueError):
        report.to_json([{"measurement": float("nan")}])

@pytest.mark.parametrize("encoding", ["pcm", "float"])
def test_silence_is_not_ready(tmp_path, encoding):
    from mix_ready import analysis
    path = str(tmp_path / "silence.wav")
    x = np.zeros((44100 * 12, 2), dtype=np.float32)
    if encoding == "pcm":
        audio.write_wav_pcm(path, x, 44100, 24)
    else:
        audio.write_wav_float(path, x, 44100)
    result = analysis.analyze(path)
    assert result["status"] == "fail"
    assert result["ready"] is False
    json.loads(report.to_json([result]), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
