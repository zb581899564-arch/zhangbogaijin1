"""Freeze the approved Windows anchor for Linux; no scientific computation here."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
ANCHOR = ROOT / 'runs/ctx-gom-capability-20261106-051509-678987'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    payload = out / 'payload'
    payload.mkdir()
    providers = []
    original_cp = (ANCHOR / 'classpath.txt').read_text('utf-8-sig').strip().split(';')
    for i, raw in enumerate(original_cp):
        original = Path(raw)
        destination = payload / 'dependencies' / ('cp-%03d' % i)
        if original.is_file():
            destination = destination.with_suffix(original.suffix)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, destination)
        else:
            shutil.copytree(original, destination)
        providers.append({'position': i, 'original': str(original),
                          'relative': destination.relative_to(payload).as_posix()})
    for name in ('source', 'overrides'):
        shutil.copytree(ANCHOR / name, payload / 'anchor' / name)
    for instance in ('20_8_5_1', '100_2_3_1'):
        shutil.copytree(ANCHOR / instance / 'inputs', payload / 'inputs' / instance)
        old = ANCHOR / instance / '14910003/FE500K-SHARE_CTX_GOM'
        for name in ('initial-population.jsonl', 'anytime.jsonl', 'run-receipt.jsonl'):
            target = payload / 'windows-reference' / instance / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old / name, target)
    command = json.loads((ANCHOR / '20_8_5_1/14910003/FE500K-SHARE_CTX_GOM/command.json').read_text('utf-8-sig'))
    write(payload / 'anchor-vm-options.json', command[1:command.index('-cp')])
    write(payload / 'classpath-providers.json', providers)
    write(payload / 'anchor-contract.json', json.loads((ANCHOR / 'protocol.json').read_text('utf-8-sig')))
    files = {p.relative_to(payload).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(payload.rglob('*')) if p.is_file()}
    write(payload / 'transfer-manifest.json', files)
    bundle = out / 'frozen-anchor.zip'
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for p in payload.rglob('*'):
            if p.is_file():
                archive.write(p, p.relative_to(payload).as_posix())
    write(out / 'bundle-identity.json', {'bytes': bundle.stat().st_size, 'sha256': sha(bundle),
                                       'files': len(files), 'anchor': str(ANCHOR)})
    print(json.dumps({'out': str(out), 'bytes': bundle.stat().st_size, 'files': len(files)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
