#!/usr/bin/env python3
"""test_plan_docs.py DIR [--pdf] - turn the volunteer test plans (DIR/*.yaml, the tester portal's format) into
documents people can follow: DIR/<platform>.md (read on GitHub) and, with --pdf, DIR/<platform>.pdf (printed by a
headless Chrome or Edge from the same content; CHROME=<path> picks the browser). The YAML stays the source - edit
it and run this again; never edit the .md or .pdf by hand.
"""
import argparse
import glob
import html
import os
import shutil
import subprocess
import sys
import tempfile

import yaml

ISSUES = "https://github.com/autobleem2/autobleem-main/issues"


def load(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def md_cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def to_markdown(plan):
    pid, ver = plan["id"], plan["version"]
    out = [f"# AutoBleem {ver} - test plan: {plan['title']}", ""]
    out += [
        "**How it works:** take **one section** (about 10 minutes), do its steps in order and tick what you saw:",
        "**OK** (it did what *Expect* says), **Problem** (it did something else - write what you saw) or **N/A** (your",
        "setup cannot do this step). Then report the section as a GitHub issue (below each section). A step that fails",
        "the same way twice is worth more than a guess about why.",
        "",
        f"Report here: {ISSUES} - one issue per section.",
        "",
        "## Before you start",
        "",
    ]
    out += [f"- {b}" for b in plan.get("before_you_start", [])]
    out += ["", "## Sections", "", "| Section | What | Minutes |", "|---|---|---|"]
    for s in plan["sections"]:
        anchor = s["id"].lower()
        out.append(f"| [{s['id']}](#{anchor}) | {md_cell(s['title'])} | {s.get('minutes', '')} |")
    for s in plan["sections"]:
        out += ["", f"## {s['id']}", "", f"**{s['title']}** - about {s.get('minutes', '?')} minutes", ""]
        if s.get("needs"):
            out += [f"**You need:** {s['needs']}", ""]
        out += ["| # | Do | Expect | Result |", "|---|---|---|---|"]
        for n, st in enumerate(s["steps"], 1):
            out.append(f"| {n} | {md_cell(st['do'])} | {md_cell(st['expect'])} | ☐ OK ☐ Problem ☐ N/A |")
        out += [
            "",
            f"**Report:** a GitHub issue titled `alpha1 {pid} {s['id']}` with your device, the version (L2 + R2 -> About)"
            " and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.",
        ]
    out.append("")
    return "\n".join(out)


CSS = """
@page { size: A4; margin: 14mm 12mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; color: #111; }
h1 { font-size: 17pt; margin: 0 0 6pt; }
h2 { font-size: 13pt; margin: 16pt 0 4pt; border-bottom: 2px solid #6a1b9a; padding-bottom: 2pt; break-after: avoid; }
p, li { line-height: 1.35; }
.how { background: #f3eef8; border-left: 4px solid #6a1b9a; padding: 6pt 8pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0; }
th, td { border: 1px solid #999; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #eee; }
tr { break-inside: avoid; }
td.n { width: 18pt; text-align: center; }
td.r { width: 62pt; white-space: nowrap; font-size: 9pt; }
.sec { break-inside: auto; }
.meta { color: #444; }
.report { font-size: 9pt; color: #333; margin-top: 3pt; }
code { background: #eee; padding: 0 2pt; }
.notes { height: 34pt; border: 1px dashed #aaa; margin-top: 4pt; font-size: 8pt; color: #888; padding: 2pt; }
"""


def to_html(plan):
    e = html.escape
    pid, ver = plan["id"], plan["version"]
    h = [f"<!doctype html><html><head><meta charset='utf-8'><title>AutoBleem {e(ver)} - {e(plan['title'])}</title>",
         f"<style>{CSS}</style></head><body>",
         f"<h1>AutoBleem {e(ver)} - test plan: {e(plan['title'])}</h1>",
         "<p class='how'><b>How it works:</b> take <b>one section</b> (about 10 minutes), do its steps in order and tick"
         " what you saw: <b>OK</b> (it did what <i>Expect</i> says), <b>Problem</b> (it did something else - write what"
         " you saw) or <b>N/A</b> (your setup cannot do this step). Then report the section as a GitHub issue: "
         f"{e(ISSUES)} - one issue per section.</p>",
         "<h2>Before you start</h2><ul>"]
    h += [f"<li>{e(b)}</li>" for b in plan.get("before_you_start", [])]
    h += ["</ul><h2>Sections</h2><table><tr><th>Section</th><th>What</th><th>Minutes</th></tr>"]
    h += [f"<tr><td>{e(s['id'])}</td><td>{e(s['title'])}</td><td>{s.get('minutes', '')}</td></tr>"
          for s in plan["sections"]]
    h.append("</table>")
    for s in plan["sections"]:
        h.append(f"<div class='sec'><h2>{e(s['id'])} - {e(s['title'])}</h2>")
        meta = f"About {s.get('minutes', '?')} minutes."
        if s.get("needs"):
            meta += f" <b>You need:</b> {e(s['needs'])}"
        h.append(f"<p class='meta'>{meta}</p>")
        h.append("<table><tr><th>#</th><th>Do</th><th>Expect</th><th>Result</th></tr>")
        for n, st in enumerate(s["steps"], 1):
            h.append(f"<tr><td class='n'>{n}</td><td>{e(st['do'])}</td><td>{e(st['expect'])}</td>"
                     "<td class='r'>&#9744; OK<br>&#9744; Problem<br>&#9744; N/A</td></tr>")
        h.append("</table><div class='notes'>Notes</div>")
        h.append(f"<p class='report'><b>Report:</b> a GitHub issue titled <code>alpha1 {e(pid)} {e(s['id'])}</code>"
                 " with your device, the version (L2 + R2 &rarr; About) and one line per step, e.g. <code>1 OK</code>,"
                 " <code>2 Problem: the screen stayed black</code>, <code>3 N/A</code>.</p></div>")
    h.append("</body></html>")
    return "\n".join(h)


def find_browser():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              shutil.which("chromium") or "", shutil.which("google-chrome") or ""):
        if p and os.path.exists(p):
            return p
    sys.exit("test_plan_docs.py: no Chrome/Edge found for --pdf (set CHROME=<path>)")


def print_pdf(browser, html_text, pdf_path):
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "plan.html")
        with open(src, "w", encoding="utf-8") as f:
            f.write(html_text)
        profile = os.path.join(tmp, "profile")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--user-data-dir={profile}", f"--print-to-pdf={os.path.abspath(pdf_path)}",
                        "file:///" + src.replace("\\", "/")], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dir")
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    browser = find_browser() if a.pdf else None
    for path in sorted(glob.glob(os.path.join(a.dir, "*.yaml"))):
        plan = load(path)
        base = os.path.splitext(path)[0]
        with open(base + ".md", "w", encoding="utf-8", newline="\n") as f:
            f.write(to_markdown(plan))
        print(f"{base}.md")
        if browser:
            print_pdf(browser, to_html(plan), base + ".pdf")
            print(f"{base}.pdf")


if __name__ == "__main__":
    main()
