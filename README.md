# autoBA

碧蓝档案（国服）协议研究：接口结构、加解密、会话机制、离线签名与日常模块 WebUI。

> **本项目仅供学习与研究。**
> 使用前请阅读 [DISCLAIMER.md](DISCLAIMER.md)。本项目不提供游戏客户端文件、账号凭据或抓包数据，
> 不鼓励用于违反游戏用户协议的行为。

## 研究内容

| 方向 | 内容 |
|---|---|
| 接口文档 | 由双向抓包明文生成的接口结构（`docs/协议/API.md` / `api_doc.json`） |
| 加解密 | packet 结构、AES-256-CBC、请求/响应 key 的明文携带方式（`ba_crypto.py`） |
| 会话机制 | SessionKey、REQUEST-ID 链、Hash=(Protocol<<32)\|N；auth 仅校验 DevId/Token/Protocol（2026-10-27 实测，`ba_session.py`） |
| 离线签名 | SHA-256 + RSA-1024 PKCS#1 v1.5 的纯 Python 复现（`sign_offline.py` + `reverse/`）；unidbg 模拟执行保留为回退路径 |
| 日常模块 | WebUI 覆盖 10 个模块：日程清票、咖啡厅、悬赏通缉、学院交流会、社交小组签到、战术对抗赛、每日免费礼包、邮箱、任务奖励、商店（11 分类）；一键清日常在后端串行执行，支持演练、关页面不中断 |

文档按用途分类，完整索引见 [docs/README.md](docs/README.md)。

## 目录

```
ba_crypto.py        AES/packet/multipart 加解密核心
ba_session.py       BA 会话客户端（auth 构造 + rid 链 + N 计数 + 落盘）
sign_offline.py     离线签名入口（默认纯 Python）
reverse/            签名逆向产物：纯 Python 实现、验证脚本、基准向量、密钥 DER、研究文档
unidbg/             unidbg 回退路径（可选，需要 Java + libairisgcore.so）
login_oracle.py     自主登录流程（发码 / 验证码登录）
decrypt_all_v2.py   抓包全量解密器（分析用；auth 已不依赖它）
webui/              FastAPI 后端 + 单页前端（10 个日常模块）；daily.py 为一键清执行器
tests/              单元测试（标准库 unittest）
scripts/            数据表生成 / 接口文档生成 / 图标导出 / 隐私自检 / 环境引导与便携打包
tables/             游戏数据表映射 + tables/full/ExcelDB 派生表
data/               客户端版本头等可入库配置
docs/               协议 / 模块 / 设计 / 参考文档
```

## 快速开始

环境要求：Windows 10+，首次运行需要联网。**无需预装 Python 或 uv**——`start_webui.bat` 会自动下载固定版本的 uv（0.13.6，带 SHA256 校验），再由 uv 准备 Python 3.12 并安装 `requirements.txt`。

```bat
:: Windows：首次运行自动准备环境，之后直接启动
start_webui.bat
```

浏览器打开 http://127.0.0.1:8800；端口冲突时用环境变量 `AUTOBA_PORT` 覆盖。

兼容性说明：

- 本机已有的其他 Python 版本不会被使用；项目只认 `.venv` 里的 Python 3.12。
- 本机已有其他 uv 版本不影响运行；脚本优先使用固定版本，下载失败时才回退系统 uv。
- 已有 `.venv` 若不是 Python 3.12 或依赖不完整，会先备份为 `.venv.bak-<时间>` 再重建。
- 路径包含空格或中文也能正常工作（脚本全程使用带引号的绝对路径）。

手动安装与启动：

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements.txt
./.venv/Scripts/python.exe -m uvicorn webui.server:app --host 127.0.0.1 --port 8800
```

本机路径（抓包目录、可选的 unidbg 工作目录 / `libairisgcore.so`）写入 `env.local.bat`，
可参考 `env.local.bat.example`；`start_webui.bat` 会自动加载该文件。

## 便携包（Windows x64）

GitHub Releases 提供 `autoBA-portable-win64.zip`：内置 Python 3.12 与全部依赖，解压后双击
`start_webui.bat` 即可启动，不需要安装 Python、uv 或联网装依赖（访问游戏服务器仍需联网）。

打包脚本：`./scripts/build_portable.ps1`（维护者需本机安装 uv）；打 `v*` 标签或手动触发
`.github/workflows/release-portable.yml` 会自动构建并发布 Release。

## 离线签名

默认使用纯 Python 实现，无需 Java、unidbg 或 `libairisgcore.so`：

```python
from sign_offline import offline_sign
sig = offline_sign(head_json + body_json)   # mode 默认 0
```

算法、两把客户端内置 RSA 私钥的提取过程与验证链见 `reverse/README.md`。
旧 unidbg 路径保留为 `offline_sign_unidbg()`，使用方式见 `unidbg/README.md`。

## 会话构造

`ba_session.py` 使用内置的 11 字段骨架构造 account/auth 请求。实测（2026-10-27）服务端只校验
`DevId`（= yostar UID）、`Token`、`Protocol` 三个字段，设备信息 / `ResUrl` / `Hash` 任意值均可。
`DevId` 与 `Token` 从 `yostar_token.json` 读取——即 `login_oracle.py` 手机号+验证码登录的产物。
因此首次使用只需完成一次自主登录，不需要抓包；仓库也不附带任何抓包数据。

`decrypt_all_v2.py` 仅用于分析历史抓包，auth 已不依赖它。

## 测试

```bash
./.venv/Scripts/python.exe -m unittest discover -s tests -v
```

## 数据表与图标

- `tables/*.json`：角色、物品、名称映射等基础表
- `tables/goods_info.json`：商店商品的 GoodsId → 名称/描述/稀有度/图标路径
- `tables/full/ExcelDB/`：WebUI 用到的派生表（商店、日程、悬赏、交流会、好感等）
- `webui/static/icons/`：游戏图标不入库，缺失时界面自动隐藏；可用 `scripts/extract_icons.py` 从自备客户端资源导出

## 边界说明

- **不含**：游戏二进制（`libairisgcore.so` 等）、账号凭据、抓包明文、密钥材料、游戏图标素材
- **包含**：协议结构文档、加解密实现、会话机制、纯 Python 离线签名实现、日常模块 WebUI
- `docs/协议/API.md` 与 `api_doc.json` 由脱敏后的抓包生成（账号使用测试号，令牌与设备字段以占位符呈现）
- 不提供账号共享、代练或商业化服务

## License

见 [LICENSE](LICENSE) 与 [DISCLAIMER.md](DISCLAIMER.md)。
