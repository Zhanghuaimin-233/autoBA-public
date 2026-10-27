#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""逐字节对比 vectors.json 中的 mode 0/1 全部向量。

用法：
  uv run --with pycryptodome python reverse/verify_pure.py
退出码：0 = 全部通过，1 = 有失败。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sign_pure import offline_sign  # noqa: E402


def main():
    vectors = json.loads(Path(__file__).with_name("vectors.json").read_text(encoding="utf-8"))
    ok = fail = 0
    for v in vectors:
        msg = bytes.fromhex(v["input_hex"])
        got = offline_sign(msg, v["mode"])
        if got == v["sig_b64"]:
            ok += 1
        else:
            fail += 1
            print(f"FAIL name={v['name']} mode={v['mode']} input={v['input_hex']}")
            print(f"  want {v['sig_b64']}")
            print(f"  got  {got}")
    print(f"PASS={ok} FAIL={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
