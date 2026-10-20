"""sign_offline.py — 离线签名（unidbg 模拟 libairisgcore.so，零游戏依赖）。

用法：
    from sign_offline import offline_sign
    sig = offline_sign(head_json + body_json)     # mode 默认 0

依赖：JDK 21+ + `unidbg/`（AiriSignRunner + jars/，见 unidbg/README.md）
      libairisgcore.so 需自行从客户端提取：默认放 capture/，或设 AUTOBA_AIRI_SO

说明：本文件仅用于协议学习与研究，签名结果确定性（同输入同输出）。
"""
import os
import subprocess

# unidbg 工作目录与 so 位置：优先环境变量，默认按仓库相对路径
WORK = os.environ.get('AUTOBA_UNIDBG_WORK', 'unidbg')
SO = os.environ.get('AUTOBA_AIRI_SO', os.path.join('capture', 'libairisgcore.so'))


def _run(text, mode):
    cp = os.path.join(WORK, 'jars') + os.sep + '*'
    sep = ';' if os.name == 'nt' else ':'
    r = subprocess.run(
        ['java', '-cp', f'{cp}{sep}.', 'AiriSignRunner', os.path.abspath(SO), text, str(mode)],
        capture_output=True, text=True, timeout=120, cwd=os.path.abspath(WORK),
        encoding='gbk', errors='replace')
    out = r.stdout
    for line in out.splitlines():
        if line.startswith('[sign('):
            return line.split('] ', 1)[1].strip()
    raise RuntimeError(f'离线签名失败: {out[-300:]} {r.stderr[-300:]}')


def offline_sign(text, mode=0):
    return _run(text, mode)


if __name__ == '__main__':
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else 'test'
    mode = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    print(f'sign("{text}", {mode}) = {offline_sign(text, mode)}')
