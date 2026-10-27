# key — 两把 RSA-1024 私钥的恢复与验证

## 存储方式（不是 DER，也不是明文 BIGNUM）

`0xf066c` 在首次 `sign` 时构造密钥：

1. `operator new(0x330)` + `memset(..., 0, 0x32D)`；
2. 从 `.rodata` 取 `0x32C` 字节，**逐字节 XOR `0xA5`**：
   - mode 0：`0xB8FE0`
   - mode 1：`0xB930C`
3. 得到 812 字符的标准 base64 文本；
4. `0xf097c`（`BIO_f_base64` + `BIO_new_mem_buf` + `BIO_set_flags(0x100)` + `BIO_read`）
   解码为 DER；
5. `d2i_PrivateKey_bio` 解析为 `EVP_PKEY`，缓存到 `0x290580`（mode 0）/ `0x2905B8`（mode 1）。

所以二进制里**没有**直接可搜的 DER 私钥，也没有未混淆的 BIGNUM；历史结论“内存无 DER
私钥”与这里一致，密钥需要按 XOR→base64→DER 的顺序还原。

复跑：

```
uv run --with pyelftools python reverse/extract_keys.py
# 生成 key_mode0.der / key_mode1.der，并打印全部参数与指纹
```

## 两把密钥参数

两把都是 `PKCS#1 RSAPrivateKey`（`version=0`，1024 位，`e=65537`），均带完整 CRT 参数。
下列十六进制为无前导零的整数值。

### mode 0

```
n    = c174751b052e5912761b98bcd46a05540fe5a71b787bbed3c86fa9712ec20e36
       d137e491083d8dd0ebe2a5bfe98c011d9ff32a31a7f3800f6406c0e8693154fb
       1caf07c8337a5b89a3c7a0fad7fe64dc584745fa24164e29c895b10a271ca8eea
       dccc81bcaa341f16daf1fdaabc8674a2a68e878a7f28422a37c8e66239412ad
d    = b514ae7d315755f6eae9200a390658a07c14ea5bd366799441bd0bad2f286427
       b9a508e51d028919b3833ec529f66c20efd4ac7d3889bc282be80a7041eef46c
       4bd3eaa3aa8ab52a0351872de7a92aa4d4484f98bc5f51a682746041239a7805b
       f1102fb42c11001ce46286de64141c3b049afdacf4969c78f8826ed70640b1d
p    = ed156da7a89afd000e2568368a442960301607b5ed55bf10fe4a46a1d90b0836
       c96f14bdfba8971e99e3a0642273047f02722a5b2a7c9623c2e9a814e21a06a3
q    = d0e3e2c423f85f25db82a3334e1a4dfd15f8d097af4ae18ef28d9b5184221cf9
       ea237196ae4e74c72cbfd07cf29bb0bc330dee9be39bfe0edcf82dead565266f
dp   = 76bd2fb133a1842addeae039c8a000b4fb005d96412a9bc9f001d5444406e173
       47098a32e8727455502f8fe9f6d2f22286601554997fd25650cd63702a196ccf
dq   = 173e03f146ff4fb6eaa1b27ef6e5be5fb69e24b77bed9d0346c1b2d2731d4894
       161533824c8ab63ba3230493a27ae843487af85da809a74f080f252cc7e9a549
qinv = 80518956d58b370e0522fb780365b856a906a3a237d85393db871865670739d9
       39f007ed3bcabac1bb5cb3cdbd0b6c3592ac952534bd94678dfc186aab589d25
sha256(n)   = 7f02032aaa909094220f44c833a93281ef919ac01ea19fcbf747c4f685f2ae21
sha256(der) = 8a902d99016e3193db7d9b36f10902683ced1ff49d3ab20328b214977a1b0ee9
```

### mode 1

```
n    = b8dbf94aa81282e5f0299924bf198c907a8ce37dbc5712b8b5b4da5091dd1f06
       e84745dfedac2b3a95dba6991bbbdddc043db4576f713fa6fed388d22cd1079d
       7544e4f603f0013bf7c8368dc14e08600d6253b87464062bd76cd7ee1c2edf80
       6d3ec320176398f9ff00c3d5ff30c314f3b41bdee9227e7ccec48fffc66f0db7
d    = 690e728d9018fd152a38a9d4ed59dabd9d38066d45a50279c0a26853d3a1a3e9
       6c065d5a969afaf24f8a4612cb6527ffcad53a715a5f34fa75e5c7e3121f3540
       babc0749208d2d7ab9f1fabb94a8d79b1dbffc5ef316fda5c099f5b02b755813
       38828d2d96ac1c522715161ac66c69c2273ddfe2e7c6ec72761efa05918bb191
p    = de3579812fe619821f147eb14c810b29f95afa2cd00c6e00f7f3e3a41856c14f
       0ea602d335946eec1cc8ff57892d625729de8bcd8a5f8d6d380c8764e347da59
q    = d4f87d6c20ae93f96361c30dd889aed2018111f2163fa7f8a06af70295e84d17
       d4aef0cfd5d134aa3af1eb313507dd6f4ed0568d7e106c8bbd3a4194f1de068f
dp   = 671581a797d3f433743daac48f8c31e4a8043799006f33bd094a4069c8ccbe62
       f195bc2bc56875c8dd55b57723714574d03ca8b8929fdf5932ae45455d56e109
dq   = 50f1e551cc962dfdd2ad1ca2cd937f13a8a8b2f66d486282580e6fb5d6de4536
       f28a4f52df34b5aca1dcc3049fe04e6478f32c8278d0ab40ed7a0fe5198cc6b7
qinv = 689cb581266101dd7a557a3106aad25772d5008fc86a733dcf8785f852dda641
       60f1a083d2b391878df4866aa5d908e445602236bdbb2bb6fb2787a0b35a2cfd
sha256(n)   = 68cce40fff0059d7d06b63bebe7a083fcc54e8b7aa7a800506f741f34b12c67f
sha256(der) = 7b612117cc916c1bd1cc0c418ebe345671c4f3d724a0cef28cfeecdd63fcc17f
```

自检（`extract_keys.py` 断言）：`p*q == n`、`e*dp ≡ 1 (mod p-1)`、`e*dq ≡ 1 (mod q-1)`、
`qinv*q ≡ 1 (mod p)` 全部通过。

## 逐字节复现 oracle

`probe_key.py` 用上述 n/d 以 PKCS#1 v1.5 + SHA-256 计算，与 `vectors.json` 对比：

```
mode0 version 0 n_bits 1024 e 65537 d_bits 1024 p*q==n True
  empty      mode=0 match=True
  1byte      mode=0 match=True
  test       mode=0 match=True
  hello      mode=0 match=True
  json_login mode=0 match=True
  short_ja   mode=0 match=True
  binary_16  mode=0 match=True
  len100     mode=0 match=True
mode1 version 0 n_bits 1024 e 65537 d_bits 1023 p*q==n True
  empty      mode=1 match=True
  1byte      mode=1 match=True
  test       mode=1 match=True
  hello      mode=1 match=True
  json_login mode=1 match=True
  short_ja   mode=1 match=True
  binary_16  mode=1 match=True
  len100     mode=1 match=True
```

≥3 组样例（完整签名见 `vectors.json`）：

| 输入 | mode | 签名前缀（hex） |
| --- | --- | --- |
| 空 | 0 | `486cb188a0bc2e3740da96c6c843a939...` |
| 空 | 1 | `9d60b86fcc5cd4174f4d30e096d713bf...` |
| `test` | 0 | `22dbc64ca0e689321926d5abb4c22a1d...` |
| `test` | 1 | `85ece5ca1c188a60c0639b88c29e6493...` |
| `{"uid":123456789,"ts":1730000000}` | 0 | `7585293bb19345b4916cba7878ee93fd...` |
| `{"uid":123456789,"ts":1730000000}` | 1 | `723aa473203ac76c3ba7d6bd01469e01...` |

（表中前缀均由 `vectors.json` 的 `sig_hex` 截取；`verify_pure.py` 做整串比较。）

## AAesKey / AAesIv 也是固定常量（2026-10-27 复核）

这两个值同样不是运行时生成，而是 `.rodata` 里 XOR 0xA5 的固定表：

| 项目 | 地址 | 长度 | 解码值 |
| --- | --- | --- | --- |
| AAesKey | `.rodata` vaddr `0xB9658` | 32 B | 客户端固定值，不随公开仓提供 |
| AAesIv | `.rodata` vaddr `0xB8E10` | 16 B | 客户端固定值，不随公开仓提供 |

证据：

- JNI_OnLoad 的 `RegisterNatives` 表（vaddr `0x25BE08`）给出：
  `getAAesKey -> 0xf022c`、`getAAesIv -> 0xf02f0`；
- `0xf022c → 0xf0d84`：`adr x10, #0xB9658`、`mov w11, #0xA5`，循环 `0x20` 次
  做 `table[i] ^ 0xA5`；
- `0xf02f0 → 0xf0e00`：`adrp/add -> 0xB8E10`、`mov w12, #0xA5`，循环 `0x10` 次
  做 `table[i] ^ 0xA5`；
- 两个构建函数只接收 sret 指针，不读参数、时间、随机数或设备信息；
- 5 次独立 JVM 调用（不同输入）输出完全一致。

复跑：

```
uv run --with pyelftools python reverse/check_aes_constants.py
```

## 备注

- 两把密钥只存在于测试用 so 中，不含任何账号/设备凭据。
- `sign_pure.py` 内嵌的是同一份 base64 DER；`extract_keys.py` 是它的来源与可复跑证明。
- 不需要 CRT 也能复现；`d` 直接参与 `pow`，1024 位运算耗时毫秒级。
