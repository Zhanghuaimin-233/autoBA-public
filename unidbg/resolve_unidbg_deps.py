"""resolve_unidbg_deps.py — 递归解析 pom 依赖并从 Maven Central 下载 jar（flat 目录）。
处理：parent 继承（properties/dependencyManagement）、${} 变量、scope 过滤（compile/runtime 必需）。
"""
import os
import re
import xml.etree.ElementTree as ET

import requests

REPO = 'https://repo1.maven.org/maven2'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jars')
os.makedirs(OUT, exist_ok=True)

NS = {'m': 'http://maven.apache.org/POM/4.0.0'}
session = requests.Session()

pom_cache = {}


def fetch_pom(g, a, v):
    key = f'{g}:{a}:{v}'
    if key in pom_cache:
        return pom_cache[key]
    url = f'{REPO}/{g.replace(".", "/")}/{a}/{v}/{a}-{v}.pom'
    r = session.get(url, timeout=30)
    if r.status_code != 200:
        pom_cache[key] = None
        return None
    root = ET.fromstring(r.text)
    pom_cache[key] = root
    return root


def resolve_version(ver, props):
    if ver is None:
        return None
    for k, val in props.items():
        ver = ver.replace(k, val)
    return ver


def collect_props(root, parent_props=None):
    props = dict(parent_props or {})
    prj = root.find('m:properties', NS)
    if prj is not None:
        for child in prj:
            tag = child.tag.split('}')[-1]
            props['${' + tag + '}'] = (child.text or '').strip()
    return props


def deps_of(root, props, scope_filter=True):
    """收集 (groupId, artifactId, version, scope)。处理 parent 的 dependencyManagement 提供缺省版本。"""
    deps = []
    # dependencyManagement 里的版本做兜底
    mgmt = {}
    dm = root.find('m:dependencyManagement', NS)
    if dm is not None:
        for dep in dm.findall('.//m:dependency', NS):
            g = dep.findtext('m:groupId', None, NS)
            a = dep.findtext('m:artifactId', None, NS)
            v = dep.findtext('m:version', None, NS)
            if g and a and v:
                mgmt[(g, a)] = resolve_version(v, props)
    depsNode = root.find('m:dependencies', NS)
    if depsNode is None:
        return deps
    for dep in depsNode.findall('m:dependency', NS):
        g = dep.findtext('m:groupId', None, NS)
        a = dep.findtext('m:artifactId', None, NS)
        v = dep.findtext('m:version', None, NS)
        scope = dep.findtext('m:scope', None, NS)
        optional = dep.findtext('m:optional', None, NS)
        if scope in ('test', 'provided'):
            continue
        if optional == 'true':
            continue
        v = resolve_version(v, props) or mgmt.get((g, a))
        if not v:
            continue
        deps.append((g, a, v, scope))
    return deps


def parent_of(root):
    p = root.find('m:parent', NS)
    if p is not None:
        return (p.findtext('m:groupId', None, NS), p.findtext('m:artifactId', None, NS),
                p.findtext('m:version', None, NS))
    return None


def process(g, a, v, props_stack, jars, depth=0, seen=None):
    if seen is None:
        seen = set()
    key = f'{g}:{a}:{v}'
    if key in seen or depth > 6:
        return
    seen.add(key)
    root = fetch_pom(g, a, v)
    if root is None:
        print(f'  [!] pom 404: {key}')
        return
    parent = parent_of(root)
    props = {}
    if parent:
        proot = fetch_pom(*parent)
        if proot is not None:
            props = collect_props(proot)
    props.update(collect_props(root, props))
    props['${project.version}'] = v
    props['${project.groupId}'] = g

    jar_url = f'{REPO}/{g.replace(".", "/")}/{a}/{v}/{a}-{v}.jar'
    dest = os.path.join(OUT, f'{a}-{v}.jar')
    if not os.path.exists(dest):
        r = session.get(jar_url, timeout=120)
        if r.status_code == 200:
            open(dest, 'wb').write(r.content)
            print(f'  [jar] {a}-{v}.jar ({len(r.content)//1024}KB)', flush=True)
        else:
            print(f'  [!] jar {r.status_code}: {a}-{v}.jar', flush=True)
            return
    else:
        print(f'  [have] {a}-{v}.jar', flush=True)

    for dg, da, dv, scope in deps_of(root, props):
        dv2 = resolve_version(dv, props)
        if dv2:
            process(dg, da, dv2, props, jars, depth + 1, seen)


print('=== 递归解析 unidbg-android 0.9.9 依赖 ===', flush=True)
process('com.github.zhkl0228', 'unidbg-android', '0.9.9', {}, set())
print('=== 完成 ===')
print('jars:', sorted(os.listdir(OUT)))
