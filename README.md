# autoBA

碧蓝档案（国服）协议研究：接口结构、加解密、会话机制与离线签名实现。

> **本项目仅供学习与研究。**
> 不提供游戏客户端文件、不包含账号凭据或抓包数据；不含任何商业化用途的授权，
> 不鼓励用于违反游戏用户协议的行为。使用本项目产生的任何后果由使用者自行承担。

## 研究内容

| 方向 | 内容 |
|---|---|
| 接口文档 | 由双向抓包明文自动生成的接口结构（`docs/API.md` / `api_doc.json`） |
| 加解密 | packet 结构、AES-256-CBC、请求/响应 key 的明文携带方式（`ba_crypto.py`） |
| 会话机制 | SessionKey、REQUEST-ID 链（响应颁发下一请求 rid）、Hash=(Protocol<<32)\|N（`ba_session.py`） |
| 离线签名 | unidbg 模拟执行客户端 native 库，PC 上获得签名结果（`unidbg/` + `sign_offline.py`） |
| 工程实现 | 会话客户端 + WebUI 展示（`webui/`） |

相关研究笔记见 `docs/`：

- `自主登录研究.md` — 手机号+验证码登录链路（yostar sdk-api → account/auth）
- `日程模块研究.md` / `咖啡厅模块研究.md` — 模块协议解剖
- `悬赏通缉.md` / `学院交流会.md` / `社交小组签到.md` — 玩法模块接口
- `数据版本校验.md` — 资源版本探针与兼容处理

## 目录

```
ba_crypto.py        AES/packet/multipart 加解密核心
ba_session.py       BA 会话客户端（rid 链 + N 计数 + 落盘）
sign_offline.py     签名封装（调用 unidbg 执行器）
unidbg/             unidbg 离线签名：AiriSignRunner.java + 依赖解析脚本
login_oracle.py     自主登录流程（发码 / 验证码登录）
webui/              FastAPI 后端 + 单页前端
scripts/            数据表生成 / 接口文档生成工具
tables/             游戏数据表映射（名称、角色、物品等）
docs/               协议研究笔记 + 接口文档
```

## 快速开始

WebUI（协议调试与数据展示）：

```bash
# Windows
start_webui.bat
# 或手动
uv run --with fastapi --with uvicorn --with requests --with pycryptodome \
    python -m uvicorn webui.server:app --host 127.0.0.1 --port 8800
```

访问 http://127.0.0.1:8800

离线签名需要自备两样环境（都不在仓库中）：

1. **`libairisgcore.so`**——从你自己合法安装的客户端中提取，放到 `capture/` 或设 `AUTOBA_AIRI_SO`
2. **unidbg 依赖 jar**——`cd unidbg && python resolve_unidbg_deps.py`（从 Maven Central 拉取）

详见 `unidbg/README.md`。`ba_session.py` 的 auth 模板还需本地抓包解密出的明文日志。

## 边界说明

- **不含**：游戏二进制（`libairisgcore.so` 等）、账号凭据、抓包明文、密钥材料
- **包含**：协议结构文档、加解密实现、会话机制、unidbg 离线签名实现
- `docs/API.md` 与 `api_doc.json` 由脱敏后的抓包生成（账号 ID 使用测试号，令牌以占位符呈现，设备字段取自测试用模拟器）
- 不提供账号共享、代练或商业化服务

## License

仅供学习交流使用。
