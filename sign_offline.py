"""sign_offline.py — 签名接口占位（本仓库不提供签名实现）。

背景：客户端签名在 native 层完成（`libairisgcore.so`，ARM64），本仓库仅保留
接口形态，供研究协议流程时对接自备的签名后端。

用法（与完整实现一致）：
    from sign_offline import offline_sign, offline_keys
    sig = offline_sign(head_json + body_json)     # -> base64 字符串
    keys = offline_keys()                          # -> {"key": ..., "iv": ...}

对接方式：保留函数签名，替换函数体即可。
"""


def offline_sign(text, mode=0):
    """返回 base64 签名（本仓库不提供实现）。"""
    raise NotImplementedError(
        '本仓库不包含签名实现：客户端签名位于 native 层（libairisgcore.so），'
        '请自行对接签名后端后替换本函数。'
    )


def offline_keys():
    """返回 {"key": ..., "iv": ...}（本仓库不提供实现）。"""
    raise NotImplementedError(
        '本仓库不包含密钥提取实现：请自行对接签名后端后替换本函数。'
    )
