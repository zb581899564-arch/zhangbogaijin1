"""Upload immutable local evidence files, verify GitHub asset digests, then publish the draft."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def api(endpoint):
    return json.loads(subprocess.check_output(['gh','api',endpoint],text=True,encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def upload(repo, commit, output, latest, resume):
    snapshot=json.loads((output/'SNAPSHOT.json').read_text('utf-8'));tag=snapshot['snapshot']
    if not resume:
        subprocess.run(['gh','release','create',tag,'--repo',repo,'--target',commit,'--draft',
            '--title','完整研究快照与失败证据（2026-11-07）','--notes-file',str(output/'RELEASE_NOTES.md')],check=True)
    releases=api(f'repos/{repo}/releases?per_page=100')
    release=next(r for r in releases if r['tag_name']==tag)
    assert release['draft'] and release['target_commitish']==commit
    expected=list(snapshot['assets'])
    for path in (output/'PROJECT_FILES.jsonl',output/'SNAPSHOT.json',latest):
        expected.append(dict(name=path.name,bytes=path.stat().st_size,sha256=sha(path)))
    for record in expected:
        path=latest if record['name']==latest.name else output/record['name']
        assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256']
        assets=api(f"repos/{repo}/releases/{release['id']}/assets?per_page=100")
        existing=next((a for a in assets if a['name']==record['name']),None)
        if existing is None:
            print('UPLOADING',record['name'],record['bytes'],flush=True)
            subprocess.run(['gh','release','upload',tag,str(path),'--repo',repo],check=True)
            assets=api(f"repos/{repo}/releases/{release['id']}/assets?per_page=100")
            existing=next(a for a in assets if a['name']==record['name'])
        assert existing['state']=='uploaded' and existing['size']==record['bytes'],record['name']
        assert existing.get('digest')=='sha256:'+record['sha256'],record['name']+' remote digest differs or is unavailable'
        record['url']=existing['browser_download_url']
        print('REMOTE_DIGEST_VERIFIED',record['name'],flush=True)
    subprocess.run(['gh','release','edit',tag,'--repo',repo,'--draft=false','--latest'],check=True)
    published=api(f"repos/{repo}/releases/{release['id']}")
    assert not published['draft'] and published['tag_name']==tag
    tag_info=api(f'repos/{repo}/git/ref/tags/{tag}')
    target=tag_info['object']
    while target['type']=='tag':
        target=api(f"repos/{repo}/git/tags/{target['sha']}")['object']
    assert target['type']=='commit' and target['sha']==commit
    result=dict(passed=True,commit=commit,tag=tag,url=published['html_url'],assets=expected,
                allRemoteSizesAndSHA256Verified=True)
    with (output/'GITHUB_RELEASE_VERIFIED.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=2)
    print('PUBLIC_RELEASE_VERIFIED',published['html_url'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('repo');p.add_argument('commit');p.add_argument('output',type=Path)
    p.add_argument('latest',type=Path);p.add_argument('--resume',action='store_true')
    a=p.parse_args();upload(a.repo,a.commit,a.output,a.latest,a.resume)
