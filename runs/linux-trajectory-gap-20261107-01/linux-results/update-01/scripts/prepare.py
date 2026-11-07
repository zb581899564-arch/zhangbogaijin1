"""Package existing evidence and explicit sources; no scientific computation on Windows."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'runs/ctx-gom-capability-20261106-051509-678987'
OUT = ROOT / 'runs/linux-trajectory-gap-20261107-01'
ARMS = ('SHARE_CTX_GOM', 'NSGA_CTX_GOM', 'PA_JOINT')


def main():
    payload = OUT / 'payload'
    payload.mkdir(parents=True, exist_ok=False)
    for stem in ('20_8_5_1', '100_2_3_1'):
        for seed in (14910003, 14910037):
            for arm in ARMS:
                source = OLD / stem / str(seed) / ('FE500K-' + arm)
                target = payload / 'historical' / stem / str(seed) / arm
                target.mkdir(parents=True)
                for name in ('anytime.jsonl', 'initial-population.jsonl', 'checkpoint-solutions.jsonl',
                             'run-receipt.jsonl', 'command.json', 'loaded-identity.jsonl'):
                    shutil.copy2(source / name, target / name)
    shutil.copy2(OLD / 'protocol.json', payload / 'historical-protocol.json')
    extra = payload / 'extra-source'
    extra.mkdir()
    for source in (ROOT / 'runs/dynamic-deep-local-20261103-184901-271850/source/ClassicAlgorithm.java',
                   ROOT / 'src/algorithms/diagnostics/pa_capability/PaLightPopulation.java',
                   ROOT / 'src/algorithms/model_global/population/PaIndividual.java'):
        shutil.copy2(source, extra / source.name)
    shutil.copytree(Path(__file__).parent, payload / 'scripts', ignore=shutil.ignore_patterns('__pycache__'))
    manifest = {p.relative_to(payload).as_posix(): {'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                for p in payload.rglob('*') if p.is_file()}
    (payload / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    with tarfile.open(OUT / 'input.tar.xz', 'w:xz', preset=3) as archive:
        archive.add(payload, arcname='payload')
    bundle = OUT / 'input.tar.xz'
    info = {'bytes': bundle.stat().st_size, 'sha256': hashlib.sha256(bundle.read_bytes()).hexdigest()}
    (OUT / 'input-identity.json').write_text(json.dumps(info), encoding='utf-8')
    print(json.dumps(info))


if __name__ == '__main__':
    main()
