# unidbg 离线签名

用 [unidbg](https://github.com/zhkl0228/unidbg)（Apache-2.0）在 PC 上模拟执行客户端的
native 签名库（`libairisgcore.so`，ARM64），直接获得 `AiriSgClient.sign()` 的结果，
无需启动游戏或模拟器。

> 仅供协议学习与研究。`libairisgcore.so` 属游戏客户端文件，**本项目不提供、不分发**，
> 请仅使用你本机合法安装的客户端中提取的文件。

## 环境

- JDK 21+
- Python 3 + `requests`（仅用于拉取依赖 jar）

## 准备

1. 拉取 unidbg 及其依赖（Maven Central，平铺到 `jars/`）：

   ```bash
   python resolve_unidbg_deps.py
   ```

2. 自备 `libairisgcore.so`（从你自己的客户端提取），放到 `../capture/libairisgcore.so`，
   或设置环境变量 `AUTOBA_AIRI_SO` 指向它。

3. 编译调用器：

   ```bash
   javac -cp "jars/*" AiriSignRunner.java
   ```

## 用法

```bash
# Windows
java -cp "jars/*;." AiriSignRunner ../capture/libairisgcore.so "headJson+bodyJson" 0
# Linux / macOS
java -cp "jars/*:." AiriSignRunner ../capture/libairisgcore.so "headJson+bodyJson" 0
```

Python 侧由 `../sign_offline.py` 封装：

```python
from sign_offline import offline_sign
sig = offline_sign(head_json + body_json)
```

## 原理与边界

- `AiriSgClient.sign(byte[], mode)` 为 native 实现：`libairisgcore.so` 通过
  RegisterNatives 注册、静态链接 OpenSSL，输出 base64 签名（确定性）。
- 签名输入是 **Head JSON 与请求体 JSON 直接拼接**后的字节串。
- 本目录只包含调用器与依赖解析脚本；不包含任何游戏二进制、不包含密钥材料。
