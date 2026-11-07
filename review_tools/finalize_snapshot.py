"""Finish publication metadata and verify the browsable mirror against original file hashes."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source,'sha256').hexdigest()


def remove_paper_extractions(records,snapshot,repository,output):
    removed=[r for r in records if r['path'].startswith('docs/') and 'sources' in Path(r['path']).parts
             and Path(r['path']).name!='资料索引.json']
    if not removed:return records
    excluded={r['path'] for r in removed};records=[r for r in records if r['path'] not in excluded]
    by_asset={}
    for row in records:by_asset.setdefault(row['asset'],set()).add(row['member'])
    for asset in snapshot['assets']:
        original=output/asset['name'];wanted=by_asset.get(asset['name'],set())
        with zipfile.ZipFile(original) as source:
            if set(source.namelist())==wanted:continue
            public=original.with_name(original.stem+'-public.zip')
            with zipfile.ZipFile(public,'x',allowZip64=True) as target:
                for info in source.infolist():
                    if info.filename not in wanted:continue
                    info._compresslevel=3
                    with source.open(info) as reader,target.open(info,'w',force_zip64=True) as writer:
                        shutil.copyfileobj(reader,writer,1024*1024)
        oldname=asset['name'];asset.update(name=public.name,bytes=public.stat().st_size,sha256=sha(public))
        for row in records:
            if row['asset']==oldname:row['asset']=public.name
    for row in removed:
        if row['gitPath']:
            result=subprocess.run(['git','ls-files','--error-unmatch',row['gitPath']],cwd=repository,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            assert result.returncode!=0,'Refusing to silently remove an existing tracked paper extraction'
            path=repository/row['gitPath'];assert path.resolve().is_relative_to(repository.resolve())
            path.unlink(missing_ok=True)
    snapshot['files']=len(records);snapshot['originalBytes']=sum(r['bytes'] for r in records)
    snapshot['uniqueObjects']=len({r['sha256'] for r in records})
    snapshot['excludedPaperExtractionPaths']=sorted(excluded)
    return records


def finish(project, repository, output, templates):
    records=[json.loads(line) for line in (output/'PROJECT_FILES.jsonl').open(encoding='utf-8')]
    snapshot=json.loads((output/'SNAPSHOT.json').read_text(encoding='utf-8'))
    records=remove_paper_extractions(records,snapshot,repository,output)
    for row in records:
        if row['path']=='.gitignore':
            row['gitPath']='snapshot/PROJECT.gitignore'
        if Path(row['path']).suffix.lower() in {'.png','.svg','.jpg','.jpeg','.pdf'} and row['bytes']<=5_000_000:
            row['gitPath']=row['path']
        if row['gitPath'] and (row['path']=='.gitignore' or Path(row['path']).suffix.lower() in {'.png','.svg','.jpg','.jpeg','.pdf'}):
            target=repository/row['gitPath'];target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(project/row['path'],target)
    with (output/'PROJECT_FILES.jsonl').open('w',encoding='utf-8') as f:
        for row in records:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    snapshot['inventorySHA256']=sha(output/'PROJECT_FILES.jsonl')
    snapshot['gitMirroredFiles']=sum(r['gitPath'] is not None for r in records)
    snapshot['gitMirroredBytes']=sum(r['bytes'] for r in records if r['gitPath'] is not None)
    snapshot['curationNotes']=['Historical .jar-suffixed POM text is preserved verbatim.',
        'Incomplete transport fragments are excluded; completed records and failure logs are retained.',
        'Generated research figures are included; full third-party papers and private reference packages are excluded.']
    (output/'SNAPSHOT.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in ('SNAPSHOT.json','PROJECT_FILES.jsonl'):
        shutil.copyfile(output/name,repository/'snapshot'/name)
    (repository/'.gitignore').write_text('__pycache__/\n*.pyc\n.env*\n*.class\n**/target/\n',encoding='utf-8')
    copies={'README-20261107.md':'README.md','RESEARCH_UPDATE_20261107.md':'RESEARCH_UPDATE_20261107.md',
        'PRO_REVIEW_PROMPT-20261107.md':'PRO_REVIEW_PROMPT.md','SNAPSHOT_README.md':'snapshot/README.md'}
    for source,target in copies.items():shutil.copyfile(templates/source,repository/target)
    for name in ('publish_snapshot.py','publish_safety.py','restore_snapshot.py','verify_public_manifest.py','finalize_snapshot.py','upload_release.py'):
        shutil.copyfile(templates/name,repository/'review_tools'/name)
    by_asset={}
    for row in records:
        by_asset.setdefault(row['asset'],{})[row['member']]=row['bytes']
    for meta in snapshot['assets']:
        path=output/meta['name'];assert path.stat().st_size==meta['bytes'] and sha(path)==meta['sha256']
        with zipfile.ZipFile(path) as archive:
            assert {i.filename:i.file_size for i in archive.infolist()}==by_asset[meta['name']]
    source_by_git={r['gitPath']:r for r in records if r['gitPath']}
    files={}
    for directory,dirs,names in os.walk(repository):
        dirs[:]=sorted(d for d in dirs if d not in {'.git','__pycache__'})
        for name in sorted(names):
            path=Path(directory)/name;relative=path.relative_to(repository).as_posix()
            if relative=='MANIFEST.json' or path.suffix=='.pyc':continue
            assert path.stat().st_size<50_000_000,relative
            record=dict(bytes=path.stat().st_size,sha256=sha(path))
            if relative in source_by_git:
                original=source_by_git[relative]
                assert (record['bytes'],record['sha256'])==(original['bytes'],original['sha256']),relative
                record['source']=original['path'];record['kind']='current-project-byte-identical'
            else:
                record['source']=None;record['kind']='review-index-tool-or-retained-historical-file'
            files[relative]=record
    manifest=dict(format=1,snapshot=snapshot['snapshot'],summary=dict(files=len(files),
        bytes=sum(r['bytes'] for r in files.values()),byTopLevel=dict(Counter(p.split('/')[0] for p in files))),files=files)
    (repository/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    notes=f'''完整研究快照，更新至2026-11-07。\n\n源码、协议、结果、失败复盘和审核提示见仓库首页。完整收录{snapshot['files']}个原项目文件，原始大小{snapshot['originalBytes']}字节；按SHA去重保存{snapshot['uniqueObjects']}个对象。全部资产SHA见SNAPSHOT.json，原路径与对象对应见PROJECT_FILES.jsonl。原始科学记录字节不改写。\n\n私密作者/参考包、第三方论文全文、临时传输、缓存、下载运行库和本地导出目录按明示规则排除。此发布未启动研究或修改默认算法。最新工作分支为1536真实FE＋36QA、零失败，固定方案停止，保留四子群与原共享。\n\n下载project-objects ZIP与两份清单，使用仓库review_tools/restore_snapshot.py恢复；只读完整性检查不执行优化器。另附最新工作分支原证据ZIP便于直接审查。'''
    (output/'RELEASE_NOTES.md').write_text(notes,encoding='utf-8')
    print(json.dumps(dict(publicFiles=len(files),publicBytes=manifest['summary']['bytes'],
        snapshotFiles=snapshot['files'],originalBytes=snapshot['originalBytes'],assets=len(snapshot['assets']),
        assetBytes=sum(a['bytes'] for a in snapshot['assets']),passed=True),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('repository',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();finish(a.project,a.repository,a.output,Path(__file__).resolve().parent)
