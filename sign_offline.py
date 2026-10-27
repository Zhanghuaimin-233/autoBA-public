"""sign_offline.py — 离线签名（默认纯 Python，无 Java / unidbg / .so 依赖）。

算法：SHA-256 + RSA-1024 PKCS#1 v1.5，mode 0/1 各一把私钥。
实现在 reverse/sign_pure.py（单文件，仅用 base64 / hashlib / 内置 pow）。

2026-10-27 之前本模块走 unidbg 模拟 libairisgcore.so。现默认纯 Python；
原实现保留为 offline_sign_unidbg()，需要回退时把 offline_sign 的函数体
改回 `return _run(text, mode)` 即可，调用方无需改动。

用法：
    from sign_offline import offline_sign, offline_keys
    sig = offline_sign(head_json + body)          # mode 默认 0
    keys = offline_keys()                          # {"key": ..., "iv": ...}

依赖：
    默认路径                          无（Python 标准库）
    offline_sign_unidbg / offline_keys  Java 21 + unidbg-work + libairisgcore.so

注意：默认路径依赖 reverse/sign_pure.py 随仓库存在（该文件内嵌两把私钥）。
"""
import importlib.util
import os
import subprocess

# unidbg 工作目录与 so 位置：优先环境变量，默认按仓库相对路径
# （本机若放在别处，设 AUTOBA_UNIDBG_WORK / AUTOBA_AIRI_SO 即可）
WORK = os.environ.get('AUTOBA_UNIDBG_WORK', 'unidbg')
SO = os.environ.get('AUTOBA_AIRI_SO', os.path.join('capture', 'libairisgcore.so'))

_HERE = os.path.dirname(os.path.abspath(__file__))
_PURE_PATH = os.path.join(_HERE, 'reverse', 'sign_pure.py')


def _load_pure_impl():
    """按文件路径加载 reverse/sign_pure.py。

    不用 sys.path.insert：那会把整个 reverse/ 暴露成可导入目录，产生全局副作用。
    """
    if not os.path.exists(_PURE_PATH):
        raise RuntimeError(
            f'纯 Python 签名实现缺失：{_PURE_PATH}；'
            f'该文件随仓库提供，缺失说明仓库不完整')
    spec = importlib.util.spec_from_file_location('_autoba_airisg_sign', _PURE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.offline_sign


_pure_sign = _load_pure_impl()


def _check_env():
    """unidbg 环境自检：缺目录/so 时报可操作的错误，而不是 WinError 267。"""
    if not os.path.isdir(WORK):
        raise RuntimeError(
            f'unidbg 工作目录不存在：{os.path.abspath(WORK)}；'
            f'请在 env.local.bat 设 AUTOBA_UNIDBG_WORK（或经 start_webui.bat 启动以自动加载）')
    if not os.path.exists(SO):
        raise RuntimeError(
            f'libairisgcore.so 不存在：{os.path.abspath(SO)}；请用 AUTOBA_AIRI_SO 指向该文件')


def _run(text, mode):
    _check_env()
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
    """返回 AiriSgClient.sign 的等价 base64 签名。

    text: str（按 UTF-8 编码）或 bytes；mode: 0/1（非 0 等价于原生 mode 1）。
    """
    return _pure_sign(text, mode)


def offline_sign_unidbg(text, mode=0):
    """回退路径：unidbg 模拟 libairisgcore.so。需要 Java 21 + unidbg + so。"""
    return _run(text, mode)


def offline_keys():
    cp = os.path.join(WORK, 'jars') + os.sep + '*'
    sep = ';' if os.name == 'nt' else ':'
    r = subprocess.run(
        ['java', '-cp', f'{cp}{sep}.', 'AiriSignRunner', os.path.abspath(SO), 'test', '0'],
        capture_output=True, text=True, timeout=120, cwd=os.path.abspath(WORK),
        encoding='gbk', errors='replace')
    key = iv = None
    for line in r.stdout.splitlines():
        if line.startswith('[AAesKey]'):
            key = line.split('] ', 1)[1].strip()
        elif line.startswith('[AAesIv ]'):
            iv = line.split('] ', 1)[1].strip()
    if not key or not iv:
        raise RuntimeError(f'AES 材料获取失败: {r.stdout[-300:]}')
    return {'key': key, 'iv': iv}


if __name__ == '__main__':
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else 'test'
    mode = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    print(f'sign("{text}", {mode}) = {offline_sign(text, mode)}')
