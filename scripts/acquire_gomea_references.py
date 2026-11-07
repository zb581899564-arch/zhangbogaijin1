"""Acquire two small author-hosted reference archives with size/provenance and safe local extraction."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_PAGE = 'https://homepages.cwi.nl/~bosman/source_code.php'
PACKAGES = ('PermutationGOMEA', 'MO-GOMEA')
MAX_FILE_BYTES = 500000000


def save(path, value):
    with path.open('x', encoding='utf-8') as target: json.dump(value, target, ensure_ascii=False, indent=2)


def response(url, method='GET'):
    result = urlopen(Request(url, method=method, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45)
    if urlparse(result.url).hostname not in ('www.cwi.nl', 'homepages.cwi.nl'):
        result.close();raise ValueError('Author reference redirected outside declared CWI hosts')
    return result


def acquire(folder, name):
    url = f'https://www.cwi.nl/~bosman/source_code/{name}_download_counter.php'
    with response(url, 'HEAD') as head:
        size = int(head.headers['Content-Length'])
        if not 0 < size < MAX_FILE_BYTES: raise ValueError('File not covered by existing small-file download authorization')
        identity = {'authorPage': AUTHOR_PAGE, 'requestedURL': url, 'resolvedURL': head.url,
            'declaredBytes': size, 'contentType': head.headers.get('Content-Type'),
            'lastModified': head.headers.get('Last-Modified'), 'etag': head.headers.get('ETag')}
    archive = folder / f'{name}.zip';hasher = hashlib.sha256();received = 0
    save(folder / f'{name}-request.json', {**identity, 'localPath': str(archive),
        'purpose': 'Read-only original algorithm implementation audit; no external upload or code execution',
        'networkRoute': 'Existing configuration; DIRECT not verified'})
    with response(url) as source, archive.open('xb') as target:
        if int(source.headers['Content-Length']) != size: raise ValueError('Reference changed between HEAD and GET')
        while True:
            chunk = source.read(65536)
            if not chunk: break
            received += len(chunk)
            if received > size: raise ValueError('Reference exceeded confirmed size')
            target.write(chunk);hasher.update(chunk)
    if received != size: raise ValueError('Downloaded reference size differs')
    destination = folder / name;destination.mkdir();members = []
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None: raise ValueError('Reference ZIP CRC failed')
        for member in package.infolist():
            pure = PurePosixPath(member.filename.replace('\\', '/'))
            if pure.is_absolute() or '..' in pure.parts or any(':' in part for part in pure.parts):
                raise ValueError('Unsafe reference member path')
            if stat.S_ISLNK(member.external_attr >> 16): raise ValueError('Reference contains a symlink')
            path = destination.joinpath(*pure.parts).resolve()
            if not path.is_relative_to(destination.resolve()): raise ValueError('Reference member outside isolated directory')
            if member.is_dir(): path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with package.open(member) as source, path.open('xb') as target: target.write(source.read())
                data = path.read_bytes();members.append({'name': member.filename, 'bytes': len(data),
                    'sha256': hashlib.sha256(data).hexdigest(), 'zipTimestamp': list(member.date_time)})
    return {**identity, 'actualBytes': received, 'archiveSHA256': hasher.hexdigest(),
        'localArchive': str(archive), 'extractionRoot': str(destination), 'members': members,
        'sourceVersion': 'Current author-hosted download; exact publication-time release not established'}


def main():
    root = ROOT / 'research/gomea_reference_audit' / datetime.now().strftime('author-sources-%Y%m%d-%H%M%S-%f')
    root.mkdir();print('GOMEA_REFERENCE_ROOT', root, flush=True);acquired = []
    try:
        for name in PACKAGES:
            result = acquire(root, name);acquired.append(result)
            print('GOMEA_REFERENCE_SAVED', name, result['actualBytes'], len(result['members']), flush=True)
    except BaseException as error:
        save(root / 'status.json', {'status': 'INCOMPLETE_RETAINED', 'error': repr(error), 'acquired': acquired});raise
    save(root / 'manifest.json', {'downloadedAtUTC': datetime.now(timezone.utc).isoformat(), 'packages': acquired,
        'totalDownloadedArchiveBytes': sum(p['actualBytes'] for p in acquired),
        'uploadedBytes': 0, 'sourceProgramsExecuted': False, 'algorithmSearchFE': 0,
        'networkSettingsChanged': False})
    save(root / 'status.json', {'status': 'COMPLETE', 'archives': len(acquired),
        'downloadedArchiveBytes': sum(p['actualBytes'] for p in acquired), 'uploadedBytes': 0, 'algorithmSearchFE': 0})


if __name__ == '__main__': main()
