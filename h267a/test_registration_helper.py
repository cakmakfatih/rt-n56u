# SPDX-License-Identifier: GPL-2.0-only
"""Emulate every syscall path of the fixed OEM port-registration helper."""
from pathlib import Path
import argparse
import struct
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_BIG_ENDIAN, UC_HOOK_INTR
from unicorn.mips_const import UC_MIPS_REG_V0, UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2, UC_MIPS_REG_A3, UC_MIPS_REG_SP

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
path = parser.parse_args().binary
for socket_error, ioctl_error in [(False, False), (True, False), (False, True)]:
    machine = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_BIG_ENDIAN)
    machine.mem_map(0x400000, 0x200000)
    machine.mem_map(0x7ffe0000, 0x10000)
    machine.reg_write(UC_MIPS_REG_SP, 0x7ffef000)
    with path.open('rb') as stream:
        elf = ELFFile(stream)
        assert elf.elfclass == 32 and not elf.little_endian
        assert not any(segment.header.p_type == 'PT_INTERP' for segment in elf.iter_segments())
        for segment in elf.iter_segments():
            if segment.header.p_type == 'PT_LOAD':
                machine.mem_write(segment.header.p_vaddr, segment.data())
        entry = elf.header.e_entry
    calls = []
    def syscall(emulator, interrupt, _):
        number = emulator.reg_read(UC_MIPS_REG_V0)
        args = [emulator.reg_read(r) for r in [UC_MIPS_REG_A0, UC_MIPS_REG_A1, UC_MIPS_REG_A2]]
        calls.append(number)
        failed, result = 0, 0
        if number == 4183:
            assert args == [2, 2, 0]
            failed, result = (1, 24) if socket_error else (0, 3)
        elif number == 4054:
            assert args[:2] == [3, 0x89f0]
            request = bytes(emulator.mem_read(args[2], 32))
            assert request[:16] == b'br0' + bytes(13)
            pointer, = struct.unpack_from('>I', request, 16)
            command, config_pointer, unused1, unused2 = struct.unpack('>4I', emulator.mem_read(pointer, 16))
            assert command == 106 and unused1 == unused2 == 0
            config = bytes(emulator.mem_read(config_pointer, 20))
            assert config == b'wlan2' + bytes(11) + b'\x00\x06\x01\x00'
            failed, result = (1, 22) if ioctl_error else (0, 0)
        elif number == 4006:
            assert args[0] == 3
        elif number == 4001:
            assert args[0] == (1 if socket_error else 2 if ioctl_error else 0)
            emulator.emu_stop()
        else:
            raise AssertionError(number)
        emulator.reg_write(UC_MIPS_REG_A3, failed)
        emulator.reg_write(UC_MIPS_REG_V0, result)
    machine.hook_add(UC_HOOK_INTR, syscall)
    machine.emu_start(entry, 0x600000, count=500)
    assert calls == ([4183, 4001] if socket_error else [4183, 4054, 4006, 4001]), calls
print('PASS: success, socket failure and ioctl failure; only fixed br0/wlan2/index6 and four allowed syscall types.')
