# algorithm — 算法族判定与逐字节证据

## 结论

`AiriSgClient.sign(byte[] data, int mode)`：

1. `digest = SHA-256(data)`（带完整 SHA-256 DigestInfo 前缀）；
2. `EM = 0x00 0x01 || 0xFF * (k-3-tLen) || 0x00 || DigestInfo`，`k = 128`，`tLen = 51`，
   `PS` 长度 74；
3. `sig = EM^d mod n`，I2OSP 为固定 128 字节（大端，保留前导零）；
4. 输出 `base64(sig)`，标准字母表、带 `=` 补齐（`EVP_EncodeBlock`）；
5. `mode 0/1` 唯一作用是选择私钥（两把不同的 RSA-1024 密钥），不改变摘要或填充；
6. 全程确定性：同一输入同一 mode 反复调用逐字节相同。

## 证据 A：还原签名块

用从库中提取的公钥做 `s^e mod n`（`check_em.py`，`e=65537`）：

```
mode 0 sig^e mod n (前 40B) = 0001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
mode 0 sig^e mod n (后 51B)  = 3031300d0609608648016503040201050004209f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
  == PKCS#1v1.5+SHA256 ? True
  == PKCS#1v1.5+SHA1   ? False
  PSS 末字节 0xbc ?     False
  EM 头 00 01 ff ?      True
mode 1 sig^e mod n (前 40B) = 0001ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
mode 1 sig^e mod n (后 51B)  = 3031300d0609608648016503040201050004209f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
  == PKCS#1v1.5+SHA256 ? True
  == PKCS#1v1.5+SHA1   ? False
  PSS 末字节 0xbc ?     False
  EM 头 00 01 ff ?      True
```

`3031300d060960864801650304020105000420` 是 SHA-256 DigestInfo 前缀
（OID `2.16.840.1.101.3.4.2.1`，后接 32 字节摘要）；`9f86d081...b0f00a08` 即
`SHA-256("test")`。

## 证据 B：静态调用链

`0xf0ba0` 的核心调用（符号由 PLT→GOT→`.rela.plt` 解析）：

| 地址 | 目标 | 含义 |
| --- | --- | --- |
| `0xf0bec` | `EVP_MD_CTX_new` | 摘要上下文 |
| `0xf0bf8` | `EVP_sha256` | 摘要算法 |
| `0xf0c10` | `EVP_DigestSignInit` | 默认 RSA 填充 = PKCS#1 v1.5 |
| `0xf0c28` | `EVP_DigestUpdate` | 喂入输入字节 |
| `0xf0c44` | `EVP_DigestSignFinal(ctx, NULL, &len)` | 取签名长度（128） |
| `0xf0c74` | `EVP_DigestSignFinal(ctx, buf, &len)` | 产出 128 字节签名 |
| `0xf08c4` | `EVP_EncodeBlock` | 标准 base64 |

## 被否定的候选（均有逐字节/结构性证据）

1. **PKCS#1 v1.5 + SHA-1**：还原出的 DigestInfo 前缀是 SHA-256 OID；与 SHA-1 EM
   比较为 False（见证据 A）。
2. **RSASSA-PSS**：PSS 的 EM 末字节应为 `0xbc`，实际为 `0x08`；且 PSS 需要随机盐，
   同一输入两次调用不会逐字节相同，而 oracle 连跑两次完全一致。
3. **mode 改变消息/摘要/填充**：同一输入 mode 0/1 还原出的 EM 完全相同，只是密钥不同；
   用 mode 0 私钥无法复现 mode 1 签名（`probe_key.py` 的逐 mode 对比）。
4. **ECDSA/其他变长签名**：所有 16 条向量签名长度恒为 128 字节，且 `s^e mod n` 呈
   PKCS#1 v1.5 结构，排除 DER 变长签名。
5. **客户端只持公钥、做“公钥签名”**：两把 PKCS#1 私钥可从 `.rodata` 解出，
   `p*q = n`、`e*d ≡ 1 (mod λ(n))`、CRT 参数全部自洽，并能逐字节复现全部向量。
6. **签名链路使用 AAesKey/AAesIv**：这两个值来自另外的 JNI 方法；sign 路径只做
   RSA + base64，输出没有二次加密/分块。

## 字节序与编码细节

- RSA 整数与签名均为大端（OpenSSL `BN_bn2bin`/`RSA_private_encrypt` 语义）。
- 签名固定 128 字节：即使最高位为 0 也不截断（I2OSP 到 k）。
- base64 为标准表（`+/`），尾部 `=` 补齐，无换行（`BIO_FLAGS_BASE64_NO_NL` 只在
  解析密钥时使用，输出由 `EVP_EncodeBlock` 产生）。
- 输入按原始字节处理；生产接口传 `str` 时按 UTF-8 编码（Java 21 默认 UTF-8，
  与 oracle 的 `text.getBytes()` 一致）。

## 复跑

```
uv run --with pycryptodome python reverse/verify_pure.py   # PASS=16 FAIL=0
python reverse/check_em.py                                 # 本文件的 EM 证据
```
