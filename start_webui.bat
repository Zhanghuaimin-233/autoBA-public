@echo off
rem 定位到本 bat 所在目录（通用，双击/任意 cwd 均可）
cd /d %~dp0
rem 本机配置（路径等），存在则加载；该文件不入库（见 .gitignore）
if exist "env.local.bat" call "env.local.bat"
uv run --with fastapi --with uvicorn --with requests --with pycryptodome python -m uvicorn webui.server:app --host 127.0.0.1 --port 8800
pause
