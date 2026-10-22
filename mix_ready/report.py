"""Text, JSON and HTML reports."""
import html
import json
import os
import time

from . import APP_NAME, STUDIO_LINE, __version__

LABEL = {"fail": "FAIL", "warn": "WARN", "ok": "OK", "info": "info"}


def _num(v, fmt):
    return "n/a" if v is None else fmt % v


def measurement_rows(m):
    return [
        ("Sample peak", _num(m["sample_peak_dbfs"], "%+.1f dBFS")),
        ("True peak", _num(m["true_peak_dbtp"], "%+.1f dBTP")),
        ("Integrated loudness", _num(m["integrated_lufs"], "%.1f LUFS")),
        ("Peak to loudness (PLR)", _num(m["plr_db"], "%.1f dB")),
        ("Loudness range (LRA)", _num(m["lra_lu"], "%.1f LU")),
        ("L/R correlation", _num(m["correlation"], "%.2f")),
        ("Low-end correlation", _num(m["low_end_correlation"], "%.2f")),
    ]


def verdict(r):
    if r["status"] == "ok":
        return "Ready for mastering."
    n = sum(f["level"] in ("fail", "warn") for f in r["findings"])
    return "Fix %d thing%s before sending." % (n, "" if n == 1 else "s")


def text(results):
    lines = []
    for r in results:
        name = os.path.basename(r["file"])
        if "error" in r:
            lines += ["== %s" % name, "  FAIL  %s" % r["error"], ""]
            continue
        lines.append("== %s  [%s] %s" % (name, LABEL[r["status"]], verdict(r)))
        lines.append("   " + r["format"]["description"])
        for k, v in measurement_rows(r["measurements"]):
            lines.append("   %-24s %s" % (k, v))
        lines.append("")
        for f in r["findings"]:
            lines.append("  %-5s %s" % (LABEL[f["level"]], f["message"]))
            if f["fix"]:
                lines.append("        Fix: %s" % f["fix"])
        if not r["findings"]:
            lines.append("  OK    No problems found.")
        lines.append("")
    lines.append(STUDIO_LINE)
    return "\n".join(lines)


def to_json(results):
    return json.dumps({"app": APP_NAME, "version": __version__, "results": results}, indent=2)


CSS = """
body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;max-width:860px;
margin:24px auto;padding:0 16px;color:#1d1d1f;background:#fff}
h1{font-size:22px}h2{font-size:18px;margin-top:32px}
table{border-collapse:collapse;margin:8px 0}td{border-bottom:1px solid #ddd;padding:5px 10px}
li{margin:6px 0}.fix{color:#444}
.fail{color:#b00020;font-weight:600}.warn{color:#a15c00;font-weight:600}
.ok{color:#1b7f3b;font-weight:600}.info{color:#555}small{color:#666}
"""


def to_html(results):
    e = html.escape
    out = ["<!doctype html><meta charset=utf-8><title>%s report</title><style>%s</style>"
           % (APP_NAME, CSS),
           "<h1>%s report</h1><small>%s %s, %s</small>"
           % (APP_NAME, APP_NAME, __version__, time.strftime("%Y-%m-%d %H:%M"))]
    for r in results:
        name = e(os.path.basename(r["file"]))
        if "error" in r:
            out.append("<h2>%s <span class=fail>FAIL</span></h2><p>%s</p>" % (name, e(r["error"])))
            continue
        out.append("<h2>%s <span class=%s>%s</span></h2><p><b>%s</b><br>%s</p>" % (
            name, r["status"], LABEL[r["status"]], e(verdict(r)), e(r["format"]["description"])))
        out.append("<table>" + "".join("<tr><td>%s</td><td>%s</td></tr>" % (e(k), e(v))
                                       for k, v in measurement_rows(r["measurements"]))
                   + "</table><ul>")
        for f in r["findings"]:
            fix = "<br><span class=fix>Fix: %s</span>" % e(f["fix"]) if f["fix"] else ""
            out.append("<li><span class=%s>%s</span> %s%s</li>" % (
                f["level"], LABEL[f["level"]], e(f["message"]), fix))
        out.append("</ul>")
    out.append("<p>%s</p>" % e(STUDIO_LINE))
    return "\n".join(out)
