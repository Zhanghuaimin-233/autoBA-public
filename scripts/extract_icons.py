"""从 Unity AssetBundle 导出 UI 图标 PNG。

跑法（需 UnityPy，Python ≤3.12）：
  python extract_icons.py <bundle...> <输出目录>
"""
import os
import sys

import UnityPy


def main():
    out = sys.argv[-1]
    bundles = sys.argv[1:-1]
    os.makedirs(out, exist_ok=True)
    total = saved = 0
    for path in bundles:
        env = UnityPy.load(path)
        for obj in env.objects:
            if obj.type.name not in ('Sprite', 'Texture2D'):
                continue
            total += 1
            try:
                data = obj.read()
                name = getattr(data, 'm_Name', None) or getattr(data, 'name', '')
                img = data.image
                if not name or img is None:
                    continue
                img.save(os.path.join(out, f'{name}.png'))
                saved += 1
            except Exception as e:
                print('skip', obj.path_id, e)
    print(f'[+] sprites {total}, saved {saved} → {out}')


if __name__ == '__main__':
    main()
