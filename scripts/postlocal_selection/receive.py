"""Verify and extract a Linux evidence delivery on Windows; no scientific computation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import zipfile


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def receive(folder):
    archive = folder / 'linux-postlocal-selection-20261106-01-evidence.zip'
    receipt = json.loads(archive.with_suffix('.receipt.json').read_text('utf-8'))
    assert archive.stat().st_size == receipt['bytes']
    assert sha(archive) == receipt['sha256']
    destination = (folder / 'linux-results').resolve()
    assert not destination.exists(), 'Never overwrite previous received evidence'
    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        assert len(names) == len(set(names)) == receipt['includedFiles']
        for entry in bundle.infolist():
            target = (destination / entry.filename).resolve()
            assert destination in target.parents and not target.exists()
            assert not stat.S_ISLNK(entry.external_attr >> 16)
        destination.mkdir()
        bundle.extractall(destination)
    manifest = json.loads((destination / 'evidence-manifest.json').read_text('utf-8'))
    for entry in manifest['files']:
        path = destination / entry['path']
        assert path.stat().st_size == entry['bytes'], str(path)
        assert sha(path) == entry['sha256'], str(path)
    result = {'passed': True, 'completedUTC': datetime.now(timezone.utc).isoformat(),
              'bytes': receipt['bytes'], 'archiveSHA256': receipt['sha256'],
              'verifiedManifestFiles': len(manifest['files']), 'destination': str(destination),
              'newSearchFE': 0, 'newDecoderCalls': 0, 'scientificAnalysisOnWindows': False}
    with (folder / 'local-receipt.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path, required=True)
    receive(parser.parse_args().folder)
