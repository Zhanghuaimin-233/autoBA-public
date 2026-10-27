#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反汇编 app 自有代码区（0xf0050..0xf11cc），标注 BL/BLR 目标符号。"""
import os
import sys

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from capstone.arm64 import ARM64_OP_IMM

SO = (sys.argv[1] if len(sys.argv) > 1
      else os.environ.get('AUTOBA_AIRI_SO') or os.path.join('capture', 'libairisgcore.so'))
START = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0xF0050
END = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0xF11CC

with open(SO, "rb") as f:
    data = f.read()
    elf = ELFFile(f)
    text = elf.get_section_by_name(".text")
    text_addr, text_off = text['sh_addr'], text['sh_offset']
    syms = []
    for sec in (elf.get_section_by_name(".dynsym"),):
        for s in sec.iter_symbols():
            if s['st_shndx'] != 'SHN_UNDEF' and s['st_value']:
                syms.append((s['st_value'], s.name))
    syms.sort()
    def sym_at(a):
        import bisect
        i = bisect.bisect_right(syms, (a, "\uffff")) - 1
        if i >= 0 and syms[i][0] <= a:
            return f"{syms[i][1]}+0x{a - syms[i][0]:x}"
        return "?"

    code = data[text_off + (START - text_addr): text_off + (END - text_addr)]
    md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    md.detail = True
    out = []
    for ins in md.disasm(code, START):
        line = f"0x{ins.address:06x}: {ins.mnemonic:<8} {ins.op_str}"
        # 分支目标注释
        if ins.mnemonic in ("bl", "b") and ins.operands and ins.operands[0].type == ARM64_OP_IMM:
            tgt = ins.operands[0].imm
            line += f"   ; -> {sym_at(tgt)}"
        out.append(line)
    print("\n".join(out))
