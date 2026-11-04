"""Enable the upstream fullscreen preference without changing sources or agreements."""
import copy
import json
import os
from pathlib import Path
import tempfile


def fullscreen_config(original):
    if not isinstance(original, dict) or not isinstance(original.get('setting'), dict):
        raise ValueError('Unrecognized LX configuration; open and close LX once first')
    changed = copy.deepcopy(original)
    changed['setting']['common.startInFullscreen'] = True
    return changed


def main():
    if os.geteuid() == 0:
        raise SystemExit('Run as the ubuntu user, not root')
    executable = b'/opt/lx-music-desktop/lx-music-desktop'
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            args = (process / 'cmdline').read_bytes().split(bytes([0]))
        except OSError:
            continue
        if args[0] == executable:
            raise SystemExit('Close LX Music normally before editing its settings')
    config = Path.home() / '.config/lx-music-desktop/LxDatas/config_v2.json'
    if config.resolve() != config:
        raise SystemExit('Refusing a symlinked configuration path')
    original_bytes = config.read_bytes()
    original = json.loads(original_bytes)
    changed = fullscreen_config(original)
    if original == changed:
        print('LX already starts fullscreen; no changes')
        return
    fd, backup = tempfile.mkstemp(prefix='config-before-fullscreen-', suffix='.json', dir=config.parent)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(original_bytes)
        stream.flush()
        os.fsync(stream.fileno())
    fd, temporary = tempfile.mkstemp(prefix='.fullscreen-', dir=config.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(changed, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        if config.read_bytes() != original_bytes:
            raise RuntimeError('LX settings changed during configuration; not overwriting')
        os.replace(temporary, config)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'Fullscreen enabled; private backup: {backup}')


if __name__ == '__main__':
    main()
