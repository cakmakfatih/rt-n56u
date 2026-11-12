# SPDX-License-Identifier: MIT
from pathlib import Path
import socket
import struct
import subprocess
import tempfile
import time


source = Path(__file__).with_name('h267a_ram_receive.c')
with tempfile.TemporaryDirectory(prefix='h267a-receive-test-') as directory:
    root = Path(directory)
    for case in ('valid', 'too-large', 'existing', 'wrong-peer', 'short-input'):
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
        output = root / (case + '.bin')
        program = root / case
        allowed = '127.0.0.2' if case == 'wrong-peer' else '127.0.0.1'
        subprocess.run(['cc', '-std=c99', '-Os', str(source), '-o', str(program),
                        '-DBIND_ADDR="127.0.0.1"', f'-DALLOWED_ADDR="{allowed}"',
                        f'-DPORT={port}', f'-DOUTPUT_PATH="{output}"'], check=True)
        if case == 'existing': output.write_bytes(b'preserve')
        process = subprocess.Popen([str(program)])
        try:
            for attempt in range(100):
                try:
                    connection = socket.create_connection(('127.0.0.1', port), timeout=.1)
                    break
                except ConnectionRefusedError:
                    time.sleep(.01)
            with connection:
                if case == 'valid':
                    data = bytes(range(256)) * 4096
                    connection.sendall(struct.pack('>I', len(data)) + data)
                    assert connection.recv(3) == b'OK\n'
                elif case == 'too-large': connection.sendall(struct.pack('>I', 20 * 1024 * 1024 + 1))
                elif case == 'existing': connection.sendall(struct.pack('>I', 128))
                elif case == 'short-input': connection.sendall(struct.pack('>I', 128) + b'x')
            code = process.wait(timeout=5)
            if case == 'valid': assert code == 0 and output.read_bytes() == data
            else: assert code != 0
            if case in ('too-large', 'wrong-peer'): assert not output.exists()
            if case == 'existing': assert output.read_bytes() == b'preserve'
        finally:
            if process.poll() is None: process.kill(); process.wait()
    print('RAM receive: exact 1MiB, bounded length, exclusive file, peer restriction, short input: PASS')
