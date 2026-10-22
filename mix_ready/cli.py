"""Command line: mix-ready FILE_OR_FOLDER... [--json out.json] [--html out.html]"""
import argparse
import os
import sys

from . import APP_NAME, __version__, audio, report
from .analysis import analyze


def collect(paths):
    files = []
    for p in paths:
        files += audio.list_audio_files(p) if os.path.isdir(p) else [p]
    return files


def run(files, progress=None):
    results = []
    for n, path in enumerate(files):
        if progress:
            progress(n, len(files), path)
        try:
            results.append(analyze(path))
        except (audio.AudioError, OSError, ValueError) as e:
            results.append({"file": path, "error": str(e), "status": "fail"})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mix-ready", description="%s %s: checks a mix before "
                                 "it goes to mastering." % (APP_NAME, __version__))
    ap.add_argument("paths", nargs="+", help="audio files or folders")
    ap.add_argument("--json", metavar="FILE", help="also write a JSON report")
    ap.add_argument("--html", metavar="FILE", help="also write an HTML report")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    files = collect(args.paths)
    if not files:
        print("No audio files found.", file=sys.stderr)
        return 2
    results = run(files)
    print(report.text(results))
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(report.to_json(results))
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(report.to_html(results))
    return 1 if any(r["status"] == "fail" for r in results) else 0
