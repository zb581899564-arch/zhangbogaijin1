"""Windows transfer-integrity verification only; scientific execution remains Linux-only."""
import argparse
import json
from pathlib import Path
import stat
import zipfile
from common import sha, write


def receive(folder):
    archive=folder/(folder.name+'-evidence.zip')
    receipt=json.loads(archive.with_suffix('.receipt.json').read_text('utf-8'))
    assert archive.stat().st_size==receipt['bytes'] and sha(archive)==receipt['sha256']
    destination=(folder/'linux-results').resolve()
    assert not destination.exists()
    with zipfile.ZipFile(archive) as bundle:
        names=bundle.namelist();assert len(names)==len(set(names))==receipt['includedFiles']
        for entry in bundle.infolist():
            target=(destination/entry.filename).resolve()
            assert destination in target.parents and not target.exists()
            assert not stat.S_ISLNK(entry.external_attr>>16)
        destination.mkdir();bundle.extractall(destination)
    manifest=json.loads((destination/'evidence-manifest.json').read_text('utf-8'))
    for entry in manifest['files']:
        path=destination/entry['path']
        assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],str(path)
    result=dict(passed=True,bytes=receipt['bytes'],archiveSHA256=receipt['sha256'],
        verifiedManifestFiles=len(manifest['files']),destination=str(destination),
        newSearchFE=0,newDecoderCalls=0,scientificAnalysisOnWindows=False)
    write(folder/'local-receipt.json',result);print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--folder',type=Path,required=True)
    receive(p.parse_args().folder)
