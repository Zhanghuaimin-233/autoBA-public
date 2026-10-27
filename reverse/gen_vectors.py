#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务 0：生成 8+ 向量，通过 unidbg oracle（AiriSignProbe，按 hex 传精确字节）签名 mode 0/1。

复跑命令（先设 AUTOBA_UNIDBG_WORK / AUTOBA_AIRI_SO，或 call env.local.bat）：
  cd <AUTOBA_UNIDBG_WORK>
  java -cp "jars/*;<reverse 目录>" AiriSignProbe "<so>" hex:<hex> <mode>
本脚本从 unidbg 目录调用同一 harness，逐条记录 stdout 与签名。
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

ORACLE_DIR = os.environ.get('AUTOBA_UNIDBG_WORK') or 'unidbg'
SO = os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so')
CP = 'jars/*' + os.pathsep + str(Path(__file__).resolve().parent)

cases = [
    {"name": "empty", "text": ""},
    {"name": "1byte", "text": "A"},
    {"name": "test", "text": "test"},
    {"name": "hello", "text": "Hello, world!"},
    {"name": "json_login", "text": "{\"uid\":123456789,\"ts\":1730000000}"},
    {"name": "short_ja", "text": "ブルーアーカイブ"},
    {"name": "binary_16", "bytes": bytes(range(16))},
    {"name": "len100", "text": "A" * 100},
]

vectors = []
for c in cases:
    data = c.get("bytes") if "bytes" in c else c["text"].encode("utf-8")
    for mode in (0, 1):
        p = subprocess.run(
            ["java", "-cp", CP, "AiriSignProbe", SO, "hex:" + data.hex(), str(mode)],
            cwd=ORACLE_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        print(f"--- {c['name']} len={len(data)} mode={mode} ret={p.returncode} ---")
        print(p.stdout)
        if p.stderr:
            print("[stderr]", p.stderr)
        sig = None
        for line in p.stdout.splitlines():
            if line.startswith("[signature] "):
                sig = line[len("[signature] "):].strip()
        if not sig:
            print(f"ERROR: no signature captured for {c['name']} mode={mode}")
            sys.exit(1)
        raw = base64.b64decode(sig)
        vectors.append({
            "name": c["name"],
            "input_hex": data.hex(),
            "mode": mode,
            "sig_b64": sig,
            "sig_hex": raw.hex(),
            "sig_len": len(raw),
        })

with open(Path(__file__).resolve().parent / "vectors.json", "w", encoding="utf-8") as f:
    json.dump(vectors, f, ensure_ascii=False, indent=2)
print(f"\nWrote {len(vectors)} vectors -> vectors.json")
