#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build the H267A TRT29 port with private calibration outside the checkout."""
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess


DRIVER = Path('trunk/proprietary/rt_wifi/rtpci/4.1.X.X/mt76x3')


def calibration_header(data):
    if len(data) != 512 or data[:2] not in (b'\x92\x75', b'\x75\x92'):
        raise ValueError('Expected a 512-byte factory EEPROM for the MT7592/MT7603 radio')
    rows = [','.join(f'0x{x:02x}' for x in data[i:i + 16]) for i in range(0, len(data), 16)]
    return ('/* Private device calibration; never write it to NVM. */\n'
            'static const UCHAR h267a_active_eeprom[512] = {\n    ' + ',\n    '.join(rows) + '\n};\n')


def private_path(path, repository):
    path = path.resolve()
    if path.is_relative_to(repository.resolve()):
        raise ValueError('Keep build output and calibration outside the Git checkout')
    return path


def cross_compile_prefix(prefix):
    compiler = shutil.which(prefix + 'gcc')
    if compiler is None:
        raise FileNotFoundError('Cross compiler not found: ' + prefix + 'gcc')
    return str(Path(compiler).absolute())[:-3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel-dir', required=True, type=Path)
    parser.add_argument('--cross-compile', required=True)
    parser.add_argument('--eeprom', required=True, type=Path)
    parser.add_argument('--work-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--lib-dir', action='append', default=[])
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    work = private_path(args.work_dir, repository)
    output = private_path(args.output, repository)
    if work.exists() or output.exists():
        raise FileExistsError('Use a new work directory and output path')
    eeprom = private_path(args.eeprom, repository)
    kernel = args.kernel_dir.resolve()
    if not (kernel / 'include/generated/autoconf.h').is_file():
        raise ValueError('The matching GPL kernel tree must be configured and prepared first')
    header = calibration_header(eeprom.read_bytes())
    cross_compile = cross_compile_prefix(args.cross_compile)
    shutil.copytree(repository / DRIVER, work, ignore=shutil.ignore_patterns('*.o', '*.ko', '*.cmd', '*.mod.c', 'Module.symvers'))
    (work / 'include/h267a_active_eeprom.h').write_text(header)
    overlay = repository / 'h267a/network-overlay'
    environment = os.environ.copy()
    environment['PATH'] = str(Path(cross_compile).parent) + os.pathsep + environment.get('PATH', '')
    if args.lib_dir:
        environment['LD_LIBRARY_PATH'] = os.pathsep.join(args.lib_dir + [environment.get('LD_LIBRARY_PATH', '')])
    subprocess.run(['cc', '-O2', 'tools/bin2h.c', '-o', 'tools/bin2h'], cwd=work, check=True)
    command = ['make', 'LINUX', '-j2', 'PLATFORM=BB_SOC', 'CHIPSET=mt7603e', 'WIFI_MODE=AP', 'ARCH=mips',
               f'KERNEL_DIR={kernel}', f'LINUX_SRC={kernel}', f'CROSS_COMPILE={cross_compile}',
               'HOSTCFLAGS=-O2 -fcommon', 'HAS_APCLI=y', 'HAS_MAC_REPEATER_SUPPORT=y', 'HAS_WDS=n', 'HAS_ATE=n',
               'CONFIG_MIPS_TC3262=y', 'HAS_DMA_RESET_SUPPORT=y', 'HAS_CAL_FREE_IC_SUPPORT=n', 'HAS_RTMP_FLASH_SUPPORT=n',
               f'KCFLAGS=-DDEFAULT_RF_OFFSET=0 -include {overlay / "trt29_network_config.h"}',
               f'LINUXINCLUDE=-I{overlay / "include"} -I{kernel / "arch/mips/include"} -I{kernel / "include"} -include {kernel / "include/generated/autoconf.h"}', 'V=1']
    with (work / 'build.log').open('w') as log:
        subprocess.run(command, cwd=work, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    module = work / 'os/linux/mt7603e_ap.ko'
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(module, output)
    print(json.dumps({'module': str(output), 'bytes': output.stat().st_size, 'build_log': str(work / 'build.log')}))


if __name__ == '__main__':
    main()
