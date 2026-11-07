"""Read-only file integrity check; performs no scientific calculation, decoding or optimization."""
import hashlib
import json
from pathlib import Path


def verify(root):
    manifest = json.loads((root/'MANIFEST.json').read_text('utf-8'))
    for name, record in manifest['files'].items():
        path = root/name
        assert path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(), name
        assert path.stat().st_size == record['bytes'], name
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256'], name
    assert len(manifest['files']) == manifest['summary']['files']
    print('PUBLIC_MANIFEST_PASSED', len(manifest['files']), 'files; no research executed')


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
