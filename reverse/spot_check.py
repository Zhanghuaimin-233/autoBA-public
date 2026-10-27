#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用两条未公开的新输入，对 oracle 与 sign_pure 做逐字节抽查（两个 mode）。"""
import base64
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sign_pure import offline_sign

ORACLE_DIR = os.environ.get('AUTOBA_UNIDBG_WORK') or 'unidbg'
SO = os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so')
CP = 'jars/*' + os.pathsep + str(Path(__file__).resolve().parent)

NEW_INPUTS = {
    "new-input-spot": b"new-input-spot",
    "utf8-chinese": "你好，2026-10-26".encode("utf-8"),
}

ok = fail = 0
for name, data in NEW_INPUTS.items():
    for mode in (0, 1):
        p = subprocess.run(
            ["java", "-cp", CP, "AiriSignProbe", SO, "hex:" + data.hex(), str(mode)],
            cwd=ORACLE_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace")
        sig = None
        for line in p.stdout.splitlines():
            if line.startswith("[signature] "):
                sig = line[len("[signature] "):].strip()
        got = offline_sign(data, mode)
        match = sig is not None and sig == got
        ok += match
        fail += (not match)
        print(f"{name} mode={mode} match={match}")
        if not match:
            print("  oracle:", sig)
            print("  pure  :", got)
print(f"PASS={ok} FAIL={fail}")
sys.exit(0 if fail == 0 else 1)
