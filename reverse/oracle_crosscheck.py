#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用原始 AiriSignRunner（未改动）交叉核对 vectors.json 中的文本类向量。

覆盖：空串、1B、test、Hello、JSON、中文、100B，各 mode 0/1。
二进制/全字节用例只能经 AiriSignProbe（hex 入参）产生，不在此脚本范围。
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

ORACLE_DIR = os.environ.get('AUTOBA_UNIDBG_WORK') or 'unidbg'
SO = os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so')
CP = 'jars/*' + os.pathsep + '.'

TEXT = {
    "empty": "",
    "1byte": "A",
    "test": "test",
    "hello": "Hello, world!",
    "json_login": "{\"uid\":123456789,\"ts\":1730000000}",
    "short_ja": "ブルーアーカイブ",
    "len100": "A" * 100,
}

vectors = json.loads(Path(__file__).with_name("vectors.json").read_text(encoding="utf-8"))
ok = fail = 0
for name, text in TEXT.items():
    for mode in (0, 1):
        p = subprocess.run(
            ["java", "-cp", CP, "AiriSignRunner", SO, text, str(mode)],
            cwd=ORACLE_DIR, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=180)
        sig = None
        for line in p.stdout.splitlines():
            if line.strip().startswith("[sign("):
                sig = line.split(")] ", 1)[1].strip()
                break
        want = next(v["sig_b64"] for v in vectors if v["name"] == name and v["mode"] == mode)
        match = sig == want
        ok += match
        fail += (not match)
        print(f"{name:10s} mode={mode} runner_match={match}")
        if not match:
            print("  runner:", sig)
            print("  vector:", want)
print(f"PASS={ok} FAIL={fail}")
sys.exit(0 if fail == 0 else 1)
