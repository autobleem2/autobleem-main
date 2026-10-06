"""Regenerate everything in files/ in the right order, so no viewer or render is left from an older model:
the parts, the universal case, the stickers, then both viewers (they read what the others wrote).
    python make_all.py"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [["make_case.py"], ["make_universal.py"], ["make_stickers.py"], ["make_viewer.py"], ["make_viewer.py", "universal"]]

for step in STEPS:
    print("== " + " ".join(step), flush=True)
    rc = subprocess.call([sys.executable] + [os.path.join(HERE, step[0])] + step[1:], cwd=HERE)
    if rc:
        sys.exit("%s failed (exit %d)" % (" ".join(step), rc))
print("all done")
