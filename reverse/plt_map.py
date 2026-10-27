#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 PLT stub 实际 adrp/ldr 的 GOT 偏移，映射到 .rela.plt 符号（不依赖顺序假设）。"""
import os
import sys

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM, ARM64_OP_MEM, ARM64_OP_REG
from elftools.elf.elffile import ELFFile

SO = (sys.argv[1] if len(sys.argv) > 1
      else os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so'))

with open(SO, "rb") as f:
    data = f.read()
    elf = ELFFile(f)
    plt = elf.get_section_by_name(".plt")
    rel = elf.get_section_by_name(".rela.plt")
    dynsym = elf.get_section_by_name(".dynsym")
    syms = list(dynsym.iter_symbols())

    got2sym = {}
    for r in rel.iter_relocations():
        got2sym[r['r_offset']] = syms[r['r_info_sym']].name

    off = plt['sh_offset']
    base = plt['sh_addr']
    size = plt['sh_size']
    code = data[off:off + size]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    insns = list(md.disasm(code, base))
    # 以 16 字节为步长，解析 adrp x16 + ldr x17,[x16,#imm]
    for i in range(0, len(insns), 4):
        group = insns[i:i + 4]
        if len(group) < 4:
            break
        adrp, ldr = group[0], group[1]
        if adrp.mnemonic != 'adrp' or ldr.mnemonic != 'ldr':
            continue
        page = adrp.operands[0].imm
        mem = ldr.operands[1]
        if mem.type == ARM64_OP_MEM:
            got = (page + mem.mem.disp) & ((1 << 64) - 1)
            name = got2sym.get(got, '?')
            print(f"plt=0x{adrp.address:x} got=0x{got:x} {name}")
