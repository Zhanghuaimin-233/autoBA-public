# autoBA

碧蓝档案（国服）协议研究：接口结构、加解密、会话机制与工程实现参考。

> **仅供学习与研究**。本项目不包含签名实现、不包含游戏客户端文件、不包含任何账号凭据。
> 使用本项目产生的任何后果由使用者自行承担；请遵守游戏用户协议与所在地法律法规。

## 研究内容

| 方向 | 内容 |
|---|---|
| 接口文档 | 由双向抓包明文自动生成的接口结构（`docs/API.md` / `api_doc.json`） |
| 加解密 | packet 结构、AES-256-CBC、请求/响应 key 的明文携带方式（`ba_crypto.py`） |
| 会话机制 | SessionKey、REQUEST-ID 链（响应颁发下一请求 rid）、Hash=(Protocol<<32)\|N（`ba_session.py`） |
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
sign_offline.py     签名接口占位（不含实现）
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

**会话与登录功能需要自备签名后端**：`sign_offline.py` 在本仓库中是接口占位，调用会抛
`NotImplementedError`；`ba_session.py` 的 auth 模板还需要本地抓包解密出的明文日志。
项目定位是协议研究的可读实现，不是开箱即用的自动化工具。

## 边界说明

- 签名实现、密钥材料、抓包明文、账号凭据均不在本仓库
- `docs/API.md` 与 `api_doc.json` 由脱敏后的抓包生成（账号 ID、令牌、设备指纹以占位符呈现）
- 不提供任何形式的账号共享、代练或商业化服务

## License

仅供学习交流使用。
