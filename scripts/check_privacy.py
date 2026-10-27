# -*- coding: utf-8 -*-
"""check_privacy.py — 提交前隐私自检（扫描 git 跟踪的全部文本文件）。

用法：
    python scripts/check_privacy.py          # 有命中则退出码 1
    python scripts/check_privacy.py -v       # 显示命中上下文行

检查项：
1. 账号真值 —— 从 yostar_credentials.json 读取（文件不存在则跳过，如公开仓）
2. 本机绝对路径 / Windows 用户名（盘符路径、C:/Users/...）
3. 疑似手机号（11 位 1[3-9] 开头，误报请人工判断）
4. 真值前缀 —— 长真值（>=32 字符）的前 8 / 12 位。完整真值比对查不出
   `v[:8] + '…'` 这类「保留前缀」式截断泄漏（2026-10-27 gen_api_doc.py 踩过），
   故单列一项；短真值（UID、手机号等）不做前缀检查，避免误报。

约定：本项目任何提交前都应跑一遍本脚本，通过后再 commit。
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS = os.path.join(ROOT, 'yostar_credentials.json')

# 自排除：本文件的规则描述会命中自身；.gitignore 含敏感文件名清单（非真值）
EXCLUDE = {'scripts/check_privacy.py', '.gitignore'}

PATH_PAT = re.compile(r'(?<![A-Za-z])[A-Za-z]:[\\/]')
PHONE_PAT = re.compile(r'(?<!\d)1[3-9]\d{9}(?!\d)')


def tracked_files():
    out = subprocess.run(['git', 'ls-files', '-z'], capture_output=True, check=True, cwd=ROOT)
    return [p.decode('utf-8', 'surrogateescape') for p in out.stdout.split(b'\0') if p]


def load_secrets():
    """真值清单：yostar_credentials.json 顶层值 + secrets 列表。"""
    try:
        c = json.load(open(CREDS, encoding='utf-8'))
    except Exception:
        return []
    vals = []
    for k, v in c.items():
        if k == 'secrets' and isinstance(v, list):
            vals += [str(x) for x in v if len(str(x)) >= 6]
        elif isinstance(v, (str, int)) and len(str(v)) >= 6:
            vals.append(str(v))
    return sorted(set(vals), key=len, reverse=True)


# 前缀检查只对足够长的真值做：短真值（11 位 UID、手机号）取 8 位前缀
# 会大面积误报，而 token / key 这类 32+ 字符的串取 8 位几乎不会撞。
PREFIX_MIN = 32


def load_secret_prefixes(secrets):
    """长真值的 8 / 12 位前缀。用来抓 `v[:8] + '…'` 这种截断泄漏。"""
    out = set()
    for s in secrets:
        if len(s) >= PREFIX_MIN:
            out.add(s[:8])
            out.add(s[:12])
    return sorted(out, key=len, reverse=True)


def main():
    verbose = '-v' in sys.argv
    secrets = load_secrets()
    prefixes = load_secret_prefixes(secrets)
    hits = []
    for path in tracked_files():
        if path in EXCLUDE:
            continue
        try:
            text = open(os.path.join(ROOT, path), 'rb').read().decode('utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            hit_full = False
            for s in secrets:
                if s in line:
                    hits.append((path, lineno, '账号真值', s[:4] + '…'))
                    hit_full = True
            if not hit_full:
                for p in prefixes:
                    if p in line:
                        # 前缀本身很短，报告里不回显内容，只给长度方便定位
                        hits.append((path, lineno, '真值前缀', f'{len(p)} 字符'))
            m = PATH_PAT.search(line)
            if m:
                hits.append((path, lineno, '绝对路径', m.group(0)))
            m = PHONE_PAT.search(line)
            if m:
                hits.append((path, lineno, '疑似手机号', m.group(0)[:3] + '****'))

    if not hits:
        print(f'[PASS] 隐私自检通过（{len(tracked_files())} 个跟踪文件，'
              f'真值规则 {len(secrets)} 条）')
        return 0

    print(f'[FAIL] 发现 {len(hits)} 处疑似隐私/本机信息：')
    for path, lineno, kind, frag in hits:
        print(f'  {path}:{lineno}  [{kind}]  {frag}')
        if verbose:
            line = open(os.path.join(ROOT, path), encoding='utf-8', errors='replace') \
                .read().splitlines()[lineno - 1]
            print(f'      {line.strip()[:160]}')
    print('\n请修复或确认后重新提交（真值应放 yostar_credentials.json，路径应相对化）。')
    return 1


if __name__ == '__main__':
    sys.exit(main())
