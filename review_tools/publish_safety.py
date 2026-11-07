"""Credential checks for an authorized public research snapshot; never print matching bytes."""
from pathlib import Path
import gzip
import lzma
import re
import shutil
import tempfile
import zipfile

SECRET = re.compile(rb'-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----|(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{24,}|github_pat_[A-Za-z0-9_]{30,}|(?<![A-Za-z0-9])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{25,}|https?://[^\s/@:\"\']{2,}:[^\s/@\"\']{4,}@[^\s/]+')
DENIED_NAMES = {'.env', 'id_rsa', 'id_ed25519', 'credentials', 'credentials.json'}


def sensitive_name(name):
    n = Path(name).name.lower()
    return n in DENIED_NAMES or n.startswith('.env.') or n.endswith(('.p12', '.pfx', '.key', '.pem'))


def scan_stream(stream, label):
    tail = b''
    while True:
        block = stream.read(1024*1024)
        if not block:
            return
        if SECRET.search(tail+block):
            raise ValueError('Credential signature; content withheld: '+label)
        tail = block[-512:]


def scan_zip(archive, label, depth=0):
    if depth > 5:
        raise ValueError('Nested archive depth requires inspection: '+label)
    for member in archive.infolist():
        if member.is_dir():
            continue
        item = label+'!'+member.filename
        if sensitive_name(member.filename) or member.flag_bits & 1:
            raise ValueError('Private/encrypted archive entry: '+item)
        with archive.open(member) as stream:
            scan_stream(stream, item)
        suffix = Path(member.filename).suffix.lower()
        if suffix in {'.zip', '.jar', '.npz'}:
            with tempfile.SpooledTemporaryFile(max_size=8*1024*1024) as temporary:
                with archive.open(member) as stream:
                    shutil.copyfileobj(stream, temporary, 1024*1024)
                temporary.seek(0)
                with zipfile.ZipFile(temporary) as child:
                    scan_zip(child, item, depth+1)
        elif suffix in {'.gz', '.xz'}:
            with archive.open(member) as stream:
                opener = gzip.open if suffix == '.gz' else lzma.open
                with opener(stream, 'rb') as expanded:
                    scan_stream(expanded, item)


def scan_archive(path):
    if path.suffix.lower() in {'.zip', '.jar', '.npz'}:
        if not zipfile.is_zipfile(path):
            if path.stat().st_size <= 5_000_000:
                path.read_bytes().decode('utf-8-sig')
                return 'Historical archive suffix contains plain text; bytes preserved'
            raise ValueError('Unrecognized archive container: '+str(path))
        with zipfile.ZipFile(path) as archive:
            scan_zip(archive, str(path))
    elif path.suffix.lower() in {'.gz', '.xz'}:
        opener = gzip.open if path.suffix.lower() == '.gz' else lzma.open
        with opener(path, 'rb') as stream:
            scan_stream(stream, str(path))
