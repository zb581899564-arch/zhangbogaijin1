"""Restore exact project bytes from this repository's public Release objects, without running research."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def restore(root, assets, output, prefix):
    snapshot = json.loads((root/'snapshot/SNAPSHOT.json').read_text('utf-8'))
    inventory = root/'snapshot/PROJECT_FILES.jsonl'
    assert digest(inventory) == snapshot['inventorySHA256'], 'Inventory SHA mismatch'
    selected = [json.loads(line) for line in inventory.open(encoding='utf-8')]
    selected = [r for r in selected if r['path'].startswith(prefix)]
    required = {r['asset'] for r in selected}
    for record in snapshot['assets']:
        if record['name'] in required:
            path = assets/record['name']
            assert path.stat().st_size == record['bytes'] and digest(path) == record['sha256'], record['name']
    output = output.resolve(); output.mkdir(parents=True, exist_ok=False)
    archives = {}
    try:
        for record in selected:
            relative = PurePosixPath(record['path'])
            assert not relative.is_absolute() and '..' not in relative.parts
            target = output.joinpath(*relative.parts)
            assert target.resolve().is_relative_to(output)
            target.parent.mkdir(parents=True, exist_ok=True)
            name = record['asset']; assert Path(name).name == name
            if name not in archives:
                archives[name] = zipfile.ZipFile(assets/name)
            h = hashlib.sha256(); size = 0
            with archives[name].open(record['member']) as source, target.open('xb') as destination:
                for block in iter(lambda: source.read(1024*1024), b''):
                    h.update(block); size += len(block); destination.write(block)
            assert h.hexdigest() == record['sha256'] and size == record['bytes'], record['path']
    finally:
        for archive in archives.values():
            archive.close()
    print('RESTORED_AND_VERIFIED', len(selected), 'files; no search or decoding')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prefix', default='')
    args = parser.parse_args()
    restore(Path(__file__).resolve().parents[1], args.assets, args.output, args.prefix)
