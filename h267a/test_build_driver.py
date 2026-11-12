# SPDX-License-Identifier: GPL-2.0-only
from pathlib import Path
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location('build_driver', Path(__file__).with_name('build_driver.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
payload = b'\x92\x75' + bytes(range(256)) + bytes(range(254))
assert len(payload) == 512
header = module.calibration_header(payload)
assert bytes(int(x, 16) for x in re.findall(r'0x([0-9a-f]{2})', header)) == payload
for invalid in (payload[:-1], payload + b'\0', b'\0' * 512):
    try:
        module.calibration_header(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid calibration accepted')
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    repository = root / 'repository'
    (repository / 'h267a').mkdir(parents=True)
    builder = repository / 'h267a/build_driver.py'
    shutil.copyfile(Path(module.__file__), builder)
    eeprom = repository / 'factory.bin'
    eeprom.write_bytes(payload)
    command = [sys.executable, '-B', str(builder), '--kernel-dir', str(root / 'kernel'),
               '--cross-compile', 'mips-linux-', '--eeprom', str(eeprom),
               '--work-dir', str(root / 'work'), '--output', str(root / 'output.ko')]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'Keep build output and calibration outside' in result.stderr, result.stderr
    assert not (root / 'work').exists(), 'Private input rejection created a work directory'
    link = root / 'linked-repository'
    link.symlink_to(repository, target_is_directory=True)
    for path in (repository / 'private-eeprom.h', link / 'private-eeprom.h'):
        try:
            module.private_path(path, repository)
        except ValueError:
            pass
        else:
            raise AssertionError('Private output inside repository was accepted')
    assert module.private_path(root / 'private-eeprom.h', repository) == root / 'private-eeprom.h'
    compiler = root / 'toolchain/bin/mips-linux-gcc'
    compiler.parent.mkdir(parents=True)
    compiler.write_text('#!/bin/sh\nexit 0\n')
    compiler.chmod(0o755)
    prior_path = os.environ['PATH']
    os.environ['PATH'] = str(compiler.parent) + os.pathsep + prior_path
    try:
        assert module.cross_compile_prefix('mips-linux-') == str(compiler)[:-3]
        assert module.cross_compile_prefix(str(compiler)[:-3]) == str(compiler)[:-3]
        prior_cwd = Path.cwd()
        os.chdir(root)
        try:
            assert module.cross_compile_prefix('./toolchain/bin/mips-linux-') == str(compiler)[:-3]
        finally:
            os.chdir(prior_cwd)
    finally:
        os.environ['PATH'] = prior_path
print('Calibration validation, private-input/output boundaries and compiler prefixes: PASS')
