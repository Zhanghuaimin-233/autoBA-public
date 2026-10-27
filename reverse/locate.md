# locate — native sign 的定位、入口与调用链

## 环境与复跑命令

- 目标库：`libairisgcore.so`（路径由 `AUTOBA_AIRI_SO` 指定）
  （2,658,312 字节，ELF64 AArch64，ET_DYN，已剥离 `.symtab`，`.dynsym` 保留 5154 项）
- 原始 oracle（未改动）：
  ```
  cd "$AUTOBA_UNIDBG_WORK"
  java -cp "jars/*;." AiriSignRunner "<so>" "test" 0
  ```
  输出 `[sign("test", 0)] <base64>`，长度 172；连跑两次完全相同；mode 1 不同但同样确定。
- 逆向 harness：`reverse/AiriSignProbe.java`（复制 AiriSignRunner 后扩展，原文件未改）。
  支持 `utf8:` / `hex:` / `file:` 输入、断点打印入口寄存器、可选指令 trace。
  ```
  javac -encoding UTF-8 -cp "jars/*" -d reverse reverse/AiriSignProbe.java
  java -cp "jars/*;reverse" AiriSignProbe "<so>" hex:74657374 0
  ```

## 模块基址与函数地址

| 项目 | 值 |
| --- | --- |
| module base | `0x12000000` |
| module size | `0x298000` |
| sign native | `0x120f0104`（模块内偏移 `0xf0104`，文件偏移同为 `0xf0104`） |
| JNI_OnLoad | `0xf0050`，dynsym size `0xb4`；sign 紧接其后 |
| 符号情况 | sign 不在 `.dynsym` 中，是 JNI_OnLoad 里 `RegisterNatives` 注册的本地函数 |

`DvmClass.findNativeFunction(emulator, "sign([BI)Ljava/lang/String;")` 返回 `0x120f0104`，
与断点命中的 PC 一致。

## 一次调用（输入/输出）

```
[module] base=0x12000000 size=0x298000 path=libairisgcore.so
[native] sign addr=0x120f0104 offset=0xf0104
[input] len=4 hex=74657374
[entry] pc=0x120f0104 x0=0xfffe1640 x1=0x2c0ee9c1 x2=0x2002fc1d x3=0x0 lr=0x7ffff0000 sp=0xe4fff700
[signature] ItvGTKDmiTIZJtWrtMIqHZZ6JvZeXvXqnHEm601LY56t9wHn2TDYToL66AUy3sKk7pHDG9dI4E4/LGpMSeYiUgyk9zWcjOzTrvfl/ywzgkxOzOpwp5LlAylb6whUddmZykEkw+dGR0xXBXMgUCJNAgSEaIRViotp98XCMLtkqmc=
[sigbytes] len=128 hex=22dbc64ca0e689321926d5abb4c22a1d967a26f65e5ef5ea9c7126eb4d4b639eadf701e7d930d84e82fae80532dec2a4ee91c31bd748e04e3f2c6a4c49e622520ca4f7359c8cecd3aef7e5ff2c33824c4eccea70a792e503295beb085475d999ca4124c3e746474c5705732050224d0204846884558a8b69f7c5c230bb64aa67
```

入口寄存器含义（AArch64 JNI）：`x0 = JNIEnv*`，`x1 = jclass`，`x2 = jbyteArray`（DVM handle），
`x3 = int mode`；`lr = 0x7ffff0000` 是模拟器返回桩地址。

## 调用链（地址 + 解析到的符号）

PLT 的符号通过 “stub 的 adrp+ldr 得到 GOT 槽 → `.rela.plt` 的 `r_offset` → 符号名” 确认，
例如 `0x24f0f0 → GOT 0x2867e0 = BIO_new_mem_buf`，`0x24f210 → GOT 0x286870 = EVP_sha256`。

```
0xf0104  JNI sign(byte[] data, int mode)
  [env+0x558] GetArrayLength              (JNI 表 idx 171)
  [env+0x5c0] GetByteArrayElements        (idx 184)
  0xf0ba0   core(data, len, mode) -> std::string
  [env+0x600] ReleaseByteArrayElements    (idx 192)
  [env+0x538] NewStringUTF                (idx 167)  // 返回 base64

0xf0ba0  core
  0xf0404   get_key(mode) -> EVP_PKEY（带 shared_ptr 缓存）
  EVP_MD_CTX_new                 @ 0xf0bec  (PLT 0x24f200)
  EVP_sha256                     @ 0xf0bf8  (PLT 0x24f210)
  EVP_DigestSignInit             @ 0xf0c10  (PLT 0x24f220)
  EVP_DigestUpdate               @ 0xf0c28  (PLT 0x24f230)
  EVP_DigestSignFinal(NULL,&len) @ 0xf0c44  (PLT 0x24f240)
  malloc(len)                    @ 0xf0c5c  (PLT 0x24f250)
  EVP_DigestSignFinal(buf,&len)  @ 0xf0c74  (PLT 0x24f240)
  0xf07dc   base64(buf, len)
  EVP_EncodeBlock                @ 0xf08c4  (PLT 0x24f180)

0xf0404  get_key(mode)
  mutex::lock / unlock            @ 0xf0474 / 0xf0484  (PLT 0x24f0d0 / 0x24f0e0)
  缓存变量: mode 0 -> 0x290580，mode 1 -> 0x2905b8
  首次调用 -> 0xf066c(mode)

0xf066c  build_key(mode)
  operator new(0x330)             @ 0xf06a0  (PLT 0x24f120)
  memset(..., 0, 0x32D)           @ 0xf06bc  (PLT 0x24f170)
  逐字节 XOR 0xA5，长度 0x32C：
      mode 0 <- .rodata 0xB8FE0
      mode 1 <- .rodata 0xB930C
  0xf097c   base64 -> DER 字节
      strlen / BIO_f_base64 / BIO_new / BIO_new_mem_buf /
      BIO_push / BIO_set_flags(0x100) / BIO_read

0xf0404  （拿到 0xf066c 返回的字节后）
  BIO_new_mem_buf                @ 0xf0510  (PLT 0x24f0f0)
  d2i_PrivateKey_bio             @ 0xf0524  (PLT 0x24f100)
  BIO_free_all                   @ 0xf0530  (PLT 0x24f110)
```

结论：`sign` 本身只做 JNI 数组/字符串搬运；真正的签名在 `0xf0ba0`，密钥解析在
`0xf0404 → 0xf066c → 0xf097c → d2i_PrivateKey_bio`。密钥材料是 `.rodata` 里
XOR 0xA5 的 base64 文本（见 `key.md`）。

## 动态 trace（traceCode）

```
java -cp "jars/*;reverse" AiriSignProbe "<so>" hex:74657374 0 2000 reverse/trace_sign_m0.txt
```

trace 范围 `0x120f0104..0x120f2104`，共 9167 条；签名结果与上面完全一致。关键指令
（方括号内为模块偏移，指令地址为运行时地址）：

```
[libairisgcore.so 0x0f0510] 0x120f0510: "bl #0x1224f0f0"   ; BIO_new_mem_buf
[libairisgcore.so 0x0f0524] 0x120f0524: "bl #0x1224f100"   ; d2i_PrivateKey_bio
[libairisgcore.so 0x0f0bf8] 0x120f0bf8: "bl #0x1224f210"   ; EVP_sha256
[libairisgcore.so 0x0f0c10] 0x120f0c10: "bl #0x1224f220"   ; EVP_DigestSignInit
[libairisgcore.so 0x0f0c28] 0x120f0c28: "bl #0x1224f230"   ; EVP_DigestUpdate
[libairisgcore.so 0x0f0c44] 0x120f0c44: "bl #0x1224f240"   ; EVP_DigestSignFinal(NULL,&len)
[libairisgcore.so 0x0f0c74] 0x120f0c74: "bl #0x1224f240"   ; EVP_DigestSignFinal(buf,&len)
[libairisgcore.so 0x0f0774] 0x120f0774: "bl #0x120f097c"   ; base64 -> DER
[libairisgcore.so 0x0f08c4] 0x120f08c4: "bl #0x1224f180"   ; EVP_EncodeBlock
```

mode 0 的密钥构建走 `0xf06fc` 分支（mode 1 走 `0xf069c`），两者都是 XOR 0xA5 后调
`0xf097c`；完整 trace 见 `trace_sign_m0.txt`。
