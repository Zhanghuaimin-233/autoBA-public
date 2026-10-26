"""login_oracle.py — 自主手机号+验证码登录（端到端，纯离线）。

流程：
  1. 输入手机号 → 构造 SendSMSReq → 离线签名 → POST user/send-sms
  2. 输入收到的验证码 → 构造 LoginReq → POST user/login → 拿新 yostar Token
签名：由 sign_offline.py 调用 unidbg 离线签名器（需自备 libairisgcore.so，见 unidbg/README.md）。
注意：若服务端风控要求滑块，send-sms 会返回错误——此时去游戏登录界面人工过一次
     滑块获取 ticket（或接 WebUI 滑块），Captcha 需带 Randstr/Ticket 重发。
跑法：uv run --with requests python login_oracle.py <手机号>
      uv run --with requests python login_oracle.py --code <验证码>
"""
import json
import os
import sys
import time

from sign_offline import offline_sign

import requests

SDK_HOST = 'https://sdk-api.yostar.cn'
# 登录凭据（yostar UID/Token/设备指纹）从本地凭据文件读取，不入库（见 .gitignore）
_CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yostar_credentials.json')
try:
    _CREDS = json.load(open(_CREDS_FILE, encoding='utf-8'))
except Exception:
    _CREDS = {}
HEAD_TEMPLATE = {
    'PID': 'CN-BA', 'Channel': 'official', 'Platform': 'android', 'Lang': 'zh',
    'DeviceID': _CREDS.get('DeviceID', 'deadbeefdeadbeef'), 'Version': '1.16.1', 'GVersionNo': '73',
    'GBuildNo': '', 'DeviceModel': '24031PN0DC',
    'RID': 'f0ec1a2b-3d4e-4f5a-6b7c-8d9e0a1b2c3d',
    'UID': _CREDS.get('UID', 1000000000),
    'Token': _CREDS.get('Token', 'dededededededededededededededededededede'),
}


def get_oracle():
    """兼容旧接口：离线签名器（无游戏依赖）。"""
    print('[签名] unidbg 离线签名（零游戏依赖）', flush=True)
    return None, None


def sdk_call(api, path, body_obj):
    body = json.dumps(body_obj, separators=(',', ':'), ensure_ascii=False)
    head = dict(HEAD_TEMPLATE, Time=int(time.time()))
    head_json = json.dumps(head, separators=(',', ':'), ensure_ascii=False)
    sig = offline_sign(head_json + body, 0)
    auth = json.dumps({'Head': head, 'Sign': sig}, separators=(',', ':'), ensure_ascii=False)
    r = requests.post(SDK_HOST + path, data=body.encode('utf-8'), headers={
        'Authorization': auth,
        'Content-Type': 'application/json',
        'User-Agent': 'okhttp/4.9.3',
    }, timeout=30)
    print(f'[HTTP] {path} -> {r.status_code}: {r.text[:300]}', flush=True)
    return r


def main():
    api, session = get_oracle()

    # 阶段 2：python login_oracle.py --code <验证码>（读取阶段 1 存的手机号）
    if len(sys.argv) >= 3 and sys.argv[1] == '--code':
        code = sys.argv[2]
        phone = json.load(open('yostar_phone.json', encoding='utf-8'))['phone']
        login_body = {'Type': 'mobile', 'OpenID': phone, 'Token': code,
                      'UserName': '', 'Secret': ''}
        r = sdk_call(api, '/user/login', login_body)
        d = json.loads(r.text)
        if d.get('Code') != 200:
            print('[!] 登录失败：', d.get('Msg'))
            return
        user = d['Data'].get('User', {})
        print('\n=== 登录成功 ===')
        print('UID:', user.get('ID'))
        print('Token:', user.get('Token'))
        print('（此 Token 即 account/auth 用的 yostar Token，长效）')
        json.dump({'uid': user.get('ID'), 'token': user.get('Token')},
                  open('yostar_token.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print('已保存 yostar_token.json')
        return

    # 阶段 1：python login_oracle.py <手机号>
    phone = sys.argv[1] if len(sys.argv) > 1 else input('手机号: ').strip()
    json.dump({'phone': phone}, open('yostar_phone.json', 'w', encoding='utf-8'))
    sms_body = {'PhoneNumber': phone, 'Scene': 'login',
                'Captcha': {'Randstr': '', 'Ticket': ''}}
    r = sdk_call(api, '/user/send-sms', sms_body)
    d = json.loads(r.text)
    if d.get('Code') != 200:
        print('[!] 发送失败：', d.get('Msg'), '— 若提示需要验证/滑块，告诉我返回内容')
        return
    print('[OK] 验证码已发送，收到后执行: uv run --with requests python login_oracle.py --code <验证码>')


if __name__ == '__main__':
    main()
