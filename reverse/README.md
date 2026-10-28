# reverse/ — AiriSg 签名逆向

`libairisgcore.so` 的 `AiriSgClient.sign(byte[], int)` 已完整还原为纯 Python。
本目录是产物与证据；生产调用在仓库根的 `sign_offline.py`（2026-10-27 起默认走纯 Python，
原 unidbg 路径保留为 `offline_sign_unidbg()`）。

## 结论

- **算法**：SHA-256 摘要 → RSA-1024 PKCS#1 v1.5 私有运算 → 128B 大端 → 标准 base64
- **密钥**：mode 0 / 1 各一把，内嵌 `.rodata`（`0xB8FE0` / `0xB930C`，各 `0x32C` 字节，
  逐字节 XOR `0xA5` → 812 字符 base64 → PKCS#1 DER）
- **AAesKey / AAesIv**：`.rodata` 固定常量（`0xB9658` / `0xB8E10`，XOR `0xA5`），
  与协议层无关——协议 key 由 `ba_crypto.gen_key_ascii()` 每请求随机生成

## 当前实现

| 文件 | 用途 |
|---|---|
| `sign_pure.py` | **当前实现**。仅依赖 `base64` / `hashlib`，内嵌两把私钥 DER，`offline_sign(text, mode)` |
| `vectors.json` | 16 条 oracle 基准向量（8 输入 × mode 0/1），由 `gen_vectors.py` 生产 |
| `key_mode0.der` / `key_mode1.der` | 从 `.rodata` 提取的两把 PKCS#1 私钥（**提取产物，运行时不读**；生产以 `sign_pure.py` 的 `_KEY_B64` 为准，换密钥要两边同步） |

## 验证链

| 脚本 | 作用 | 依赖 |
|---|---|---|
| `verify_pure.py` | 逐字节比对全部 16 条向量 | 无（纯 Python） |
| `probe_key.py` | 用 DER 私钥独立复现向量 | 无（纯 Python） |
| `gen_vectors.py` | 用 unidbg oracle 重新生成 `vectors.json` | Java + unidbg + so |
| `oracle_crosscheck.py` | 用**原始未改动的** `AiriSignRunner` 交叉核对 14 条文本向量 | Java + unidbg + so |
| `spot_check.py` | 未公开新输入的 oracle ↔ pure 抽查 | Java + unidbg + so |

## 静态分析

| 脚本 | 作用 |
|---|---|
| `extract_keys.py` | 从 `.rodata` 提取两把 RSA 私钥（XOR `0xA5` → base64 → DER） |
| `disasm.py` | 反汇编指定地址区间，标注 BL 目标符号 |
| `plt_map.py` | PLT stub → `.rela.plt` 符号映射 |
| `check_em.py` | 用公钥还原 EM，确认 PKCS#1 v1.5 结构 |
| `AiriSignProbe.java` | unidbg harness（复制 `AiriSignRunner` 后扩展 hex/file 入参、trace、断点） |

## 研究文档

- `algorithm.md` — 算法族判定（SHA-256 + PKCS#1 v1.5；排除 SHA-1 与 PSS）
- `key.md` — 两把密钥的恢复过程与参数指纹
- `locate.md` — native 入口定位、调用链、动态 trace

## 环境变量

| 变量 | 含义 |
|---|---|
| `AUTOBA_AIRI_SO` | `libairisgcore.so` 路径（仅需 Java 的脚本用） |
| `AUTOBA_UNIDBG_WORK` | unidbg 工作目录（含 `AiriSignRunner.class` + `jars/`） |

可在仓库根 `env.local.bat` 中设置（该文件不入库，`start_webui.bat` 会自动加载），或直接设置进程环境变量。

## 复跑

```bash
# 不需要 Java
./.venv/Scripts/python.exe reverse/verify_pure.py       # PASS=16 FAIL=0
./.venv/Scripts/python.exe reverse/probe_key.py         # 16/16 match=True

# 需要 Java + so
./.venv/Scripts/python.exe reverse/oracle_crosscheck.py # PASS=14 FAIL=0
./.venv/Scripts/python.exe reverse/spot_check.py        # PASS=4 FAIL=0
./.venv/Scripts/python.exe reverse/gen_vectors.py       # 重生成 vectors.json，哈希应不变

# 静态分析
./.venv/Scripts/python.exe reverse/extract_keys.py
./.venv/Scripts/python.exe reverse/disasm.py <so> 0xf0104 0xf0300
```

## 未入库的本机产物

由 `.gitignore` 屏蔽，不进版本库：

- `*.class` — `javac` 编译 `AiriSignProbe.java` 的产物
- `trace_sign_m0.txt` — 动态 trace，可用 `AiriSignProbe` 的 `traceLenHex` / `traceFile` 参数重现

AAesKey / AAesIv 的具体值不随公开仓提供；它们与协议层无关，也不参与签名。
