"""Small code transfer and pre-run protocol, preserving the first evidence payload."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile
from prepare import ROOT, OUT


def main():
    target=OUT/'update-01';target.mkdir()
    shutil.copytree(Path(__file__).parent,target/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(ROOT/'src/algorithms/diagnostics/trajectory_gap',target/'java')
    (target/'frozen').mkdir()
    shutil.copy2(ROOT/'runs/qpa-capability-pilot-20261106-025546-344483/source/PaPopulation.java',target/'frozen/PaPopulation.java')
    plan=dict(version='TRAJECTORY_GAP_READONLY_V1',instance='100_2_3_1',seed=14910003,
        arms=['SHARE_CTX_GOM','NSGA_CTX_GOM','PA_JOINT'],captureFEPerArm=500000,engineeringFEPerArm=30000,
        maximumActualSearchFEIncludingEngineering=1590000,maximumAutomaticCheckpointQA=60000,
        execution='Linux JDK17 --release8; single JVM sequential nice10; no time superiority claim',
        precondition='Step1 existing fronts; shared initial100; unchanged base class hashes',
        observerAcceptance='First30000 paid digest against original search; all old public checkpoints and paid representative genomes',
        graphMeaning='Exact four-vector/objective schedule reuse; not object lineage or causal credit',
        observation='Every paid candidate, archive admission, GOM/PA acceptance, program and working population ends',
        scientificLimits=['One existing instance and seed','Known 200-to100 selection loss already unsupported',
            'No donor ratio, request weighting, family refresh, pruned edit transfer, or regional preference repeat'],
        step3Gate='Only a concrete untested program difference with a falsifiable ordinary control warrants a separately frozen micro-test; otherwise stop and state limits',
        mainlineChanged=False,newSeeds=False,defaultBackgroundExperiments=False)
    (target/'protocol.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={p.relative_to(target).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in target.rglob('*') if p.is_file()}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with tarfile.open(OUT/'update-01.tar.xz','w:xz',preset=3) as a:a.add(target,arcname='update-01')
    bundle=OUT/'update-01.tar.xz'
    print(json.dumps(dict(bytes=bundle.stat().st_size,sha256=hashlib.sha256(bundle.read_bytes()).hexdigest())))


if __name__=='__main__':main()
