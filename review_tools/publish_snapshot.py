"""Preserve all eligible project bytes in deduplicated Release assets plus a browseable Git mirror."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import zipfile
from publish_safety import SECRET, sensitive_name, scan_archive

TEXT = {'.java','.py','.md','.json','.jsonl','.csv','.tsv','.xml','.txt','.patch','.diff','.log','.properties','.sh','.c','.h','.jl','.yaml','.yml','.toml','.ini','.pareto'}
SKIP = {'.git','.idea','__pycache__','target','runtime','downloads'}
STORED = {'.zip','.jar','.gz','.xz','.npz','.png','.jpg','.jpeg','.jfr'}
PRIVATE_PREFIXES = ('private-qgomea-', 'author-sources-', 'native-semantics-', 'private-publications-')


def excluded(relative):
    parts = relative.parts
    if relative.name.endswith('.incomplete.zip') or relative.suffix.lower() == '.partial':
        return 'incomplete temporary transfer; completed scientific artifacts and failure logs retained'
    if parts[0] in {'review','tmp'}:
        return 'local export staging or temporary extraction'
    if any(p in SKIP for p in parts) or relative.suffix.lower() == '.pyc':
        return 'rebuildable tooling, dependency download or cache'
    if parts[0] == 'research' and any(p.startswith(PRIVATE_PREFIXES) for p in parts):
        return 'private author/reference package excluded by project rules'
    if parts[0] == 'docs' and 'sources' in parts and relative.name != '资料索引.json':
        return 'third-party paper text or page extraction excluded from public review'
    if relative.suffix.lower() == '.pdf' and not (parts[0] == 'runs' and 'figures' in parts):
        return 'third-party literature PDF excluded from public review'
    if sensitive_name(relative.name):
        return 'credential or private key filename'
    return None


def browse(relative, size):
    if relative.suffix.lower() not in TEXT and relative.name not in {'.gitignore','LICENSE'}:
        return False
    if relative.parts[0] != 'runs':
        return size <= 5_000_000
    if relative.suffix.lower() in {'.java','.py','.md','.xml','.txt','.properties','.patch','.diff','.sh','.log','.c','.h','.jl'}:
        return size <= 1_000_000
    limit = 1_000_000 if 'analysis' in relative.parts or relative.name in {'protocol.json','identity.json','receipt.json','accounting.json','independent-audit.json','delivery-manifest.json'} else 128_000
    return size <= limit


def candidates(project):
    for directory, dirs, files in os.walk(project, followlinks=False):
        dirs.sort(); files.sort()
        base = Path(directory)
        dirs[:] = [d for d in dirs if not excluded((base/d).relative_to(project))]
        for name in files:
            path = base/name; relative = path.relative_to(project)
            if excluded(relative) or path.is_symlink():
                continue
            assert path.resolve().is_relative_to(project.resolve()), relative
            yield path, relative


class Assets:
    def __init__(self, folder):
        self.folder = folder; self.archive = None; self.records = []; self.names = {}

    def resume(self, inventory):
        for row in inventory:
            self.names[row['sha256']] = {k: row[k] for k in ('asset','member')}
        for path in sorted(self.folder.glob('project-objects-*.zip')):
            with zipfile.ZipFile(path) as z:
                expected = {v['member'] for v in self.names.values() if v['asset'] == path.name}
                assert set(z.namelist()) == expected, path.name
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream,'sha256').hexdigest()
            self.records.append(dict(name=path.name,bytes=path.stat().st_size,sha256=digest))

    def next(self):
        if self.archive is not None:
            self.close()
        self.name = f'project-objects-{len(self.records)+1:03d}.zip'
        self.path = self.folder/self.name
        self.archive = zipfile.ZipFile(self.path, 'x', zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True)
        print('ASSET_OPEN', self.name, flush=True)

    def close(self):
        self.archive.close(); self.archive = None
        digest = hashlib.file_digest(self.path.open('rb'), 'sha256').hexdigest()
        self.records.append(dict(name=self.name, bytes=self.path.stat().st_size, sha256=digest))
        print('ASSET_CLOSED', self.name, self.path.stat().st_size, flush=True)

    def put(self, path, digest):
        if digest in self.names:
            return self.names[digest]
        if self.archive is None or self.archive.fp.tell() >= 384_000_000:
            self.next()
        member = 'objects/'+digest; check = hashlib.sha256()
        info = zipfile.ZipInfo(member); info.compress_type = zipfile.ZIP_STORED if path.suffix.lower() in STORED else zipfile.ZIP_DEFLATED
        info._compresslevel = 3
        with path.open('rb') as source, self.archive.open(info, 'w', force_zip64=True) as target:
            for block in iter(lambda: source.read(1024*1024), b''):
                if SECRET.search(getattr(self,'tail',b'')+block):
                    raise ValueError('Credential signature; content withheld: '+str(path))
                self.tail = block[-512:]
                check.update(block); target.write(block)
        self.tail = b''
        assert check.hexdigest() == digest, 'Source changed during copy: '+str(path)
        self.names[digest] = dict(asset=self.name, member=member)
        return self.names[digest]


def main(project, repository, output, resume=False):
    started = time.monotonic(); output.mkdir(exist_ok=resume)
    assets = Assets(output); count = rawbytes = mirrored = mirrorbytes = 0
    inventory = output/'PROJECT_FILES.jsonl'
    previous = [json.loads(line) for line in inventory.open(encoding='utf-8')] if resume else []
    known = {r['path']:r for r in previous}; notes=[]
    if resume:
        assets.resume(previous)
        count=len(previous);rawbytes=sum(r['bytes'] for r in previous)
        mirrored=sum(r['gitPath'] is not None for r in previous)
        mirrorbytes=sum(r['bytes'] for r in previous if r['gitPath'] is not None)
        print('RESUMING_VERIFIED_PARTS',count,len(assets.records),flush=True)
    with inventory.open('a' if resume else 'x', encoding='utf-8') as manifest:
        for path, relative in candidates(project):
            initial = path.stat()
            with path.open('rb') as source:
                digest = hashlib.file_digest(source,'sha256').hexdigest()
            if relative.as_posix() in known:
                assert known[relative.as_posix()]['sha256']==digest, 'Previously staged source changed: '+str(relative)
                continue
            if digest not in assets.names:
                note=scan_archive(path)
                if note:notes.append(dict(path=relative.as_posix(),note=note))
            assert path.stat().st_size == initial.st_size and path.stat().st_mtime_ns == initial.st_mtime_ns
            stored = assets.put(path, digest)
            mirror = browse(relative, initial.st_size)
            dest = relative.as_posix()
            if dest in {'README.md','AGENTS.md'}:
                dest = 'PROJECT_'+dest
            if mirror:
                target = repository/dest; target.parent.mkdir(parents=True, exist_ok=True)
                # Existing reviewed files are updated, while all earlier versions remain in Git history.
                shutil.copyfile(path, target); mirrored += 1; mirrorbytes += initial.st_size
            manifest.write(json.dumps(dict(path=relative.as_posix(),bytes=initial.st_size,sha256=digest,
                **stored,gitPath=dest if mirror else None),ensure_ascii=False)+'\n')
            count += 1; rawbytes += initial.st_size
            if count % 2000 == 0:
                print('PROGRESS', count, rawbytes, 'unique',len(assets.names), flush=True)
    if assets.archive is not None:
        assets.close()
    summary = dict(snapshot='research-snapshot-20261107', files=count, originalBytes=rawbytes,
        uniqueObjects=len(assets.names), gitMirroredFiles=mirrored, gitMirroredBytes=mirrorbytes,
        assets=assets.records, inventorySHA256=hashlib.sha256(inventory.read_bytes()).hexdigest(),
        secondsThisInvocation=time.monotonic()-started, resumedFiles=len(previous), historicalContainerNotes=notes,
        credentialScanPassed=True, scientificSearchStarted=False,
        scope='Current project tree; excluded original Li evidence sibling, private reference packages, literature full text, export staging, caches, downloaded runtimes and temporary files.',
        exclusions=dict(topLevel=['review','tmp'], directoryNames=sorted(SKIP), privateResearchPrefixes=PRIVATE_PREFIXES,
                        temporaryTransferPatterns=['*.incomplete.zip','*.partial'],
                        thirdPartyFullText=['docs/sources except index','literature PDFs; generated runs/figures PDFs included'], credentialNamesExcluded=True))
    (output/'SNAPSHOT.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dest = repository/'snapshot'; dest.mkdir(exist_ok=True)
    for name in ('PROJECT_FILES.jsonl','SNAPSHOT.json'):
        shutil.copyfile(output/name,dest/name)
    print('SNAPSHOT_COMPLETE', json.dumps(summary,ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('project',type=Path);parser.add_argument('repository',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();main(args.project.resolve(),args.repository.resolve(),args.output.resolve(),args.resume)
