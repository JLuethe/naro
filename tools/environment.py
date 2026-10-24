"""Read-only native/runtime provenance shared by follow-up validators."""
import hashlib
import os
from pathlib import Path
import platform
import subprocess


def command(args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        return 'unavailable: ' + str(error)


def snapshot():
    databases = {}
    for name in ['/usr/share/misc/magic.mgc', '/usr/share/file/magic.mgc',
                 '/usr/share/file/misc/magic.mgc']:
        path = Path(name).resolve()
        if path.is_file():
            with path.open('rb') as stream:
                databases[str(path)] = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'system': platform.platform(), 'machine': platform.machine(),
            'libc': platform.libc_ver(), 'python': platform.python_version(),
            'tmux': command(['tmux', '-V']), 'locale_inventory': command(['locale', '-a']),
            'file': command(['file', '--version']), 'magic_databases': databases,
            'locpath': os.environ.get('LOCPATH')}
