# SPDX-License-Identifier: GPL-2.0-only
"""Build the fixed MIPS port-registration helper outside the Git checkout."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess

from build_driver import cross_compile_prefix, private_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cross-compile', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--lib-dir', action='append', default=[])
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    output = private_path(args.output, repository)
    if output.exists():
        raise FileExistsError('Use a new output path')
    prefix = cross_compile_prefix(args.cross_compile)
    environment = os.environ.copy()
    if args.lib_dir:
        environment['LD_LIBRARY_PATH'] = os.pathsep.join(args.lib_dir + [environment.get('LD_LIBRARY_PATH', '')])
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([prefix + 'gcc', '-Os', '-mabi=32', '-EB', '-march=mips32r2', '-msoft-float',
                    '-mno-abicalls', '-fno-pic', '-fno-stack-protector', '-nostdlib', '-static',
                    '-Wl,--build-id=none', '-Wl,-e,_start', '-o', str(output),
                    str(Path(__file__).with_name('h267a-register-wlan2.c'))], env=environment, check=True)
    subprocess.run([prefix + 'strip', '--strip-all', str(output)], env=environment, check=True)
    print(json.dumps({'helper': str(output), 'bytes': output.stat().st_size,
                      'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
