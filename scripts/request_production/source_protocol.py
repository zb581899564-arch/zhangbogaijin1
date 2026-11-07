"""Freeze provenance capture before inspecting request outcomes."""
import argparse
from pathlib import Path
import subprocess
from common import ANCHOR, SOURCE, STEMS, SEEDS, JAVA, JAVAC, linux, read, sha, write


def freeze(root):
    linux()
    assert read(SOURCE / 'delivery-acceptance.json')['passed']
    contexts = []
    for stem in STEMS:
        for index, seed in enumerate(SEEDS):
            path = SOURCE / 'capture' / stem / str(seed) / 'capture.json'
            value = read(path)
            contexts.append(dict(instance=stem, seed=seed, family=index % 4,
                before=value['beforeGlobalFE'], after=value['afterGlobalFE'],
                sourceCapture=str(path), sourceSHA256=sha(path)))
    value = dict(version='REAL_SHARED_REQUEST_CAPTURE-v1', instances=STEMS, seeds=SEEDS,
        contexts=contexts, sourceAdditionalAttemptedFE=sum(c['after'] for c in contexts),
        historicalSourceFE=3000000, source='Frozen mature-donor Linux FULL prefixes',
        capture='All actual compose requests in the previously fixed mature global phase',
        sampling='Per source seed select family seedIndex%4 and its first four requests; keep all outcomes; no benefit-based replacement',
        probeUpperBoundFE=24*4*512,
        barrier='All requests, parents, models, pools and background used only at the common recorded POST_GLOBAL barrier; this is conditional batch replay, not immediate online feedback',
        shuffle='Within each source and the selected fixed FA family, cyclic shift of the four observed cap/eta pairs; all existed by common barrier',
        actualRequest='cap = parent Cmax * [0.9,1,1.1][cycle//3]; eta=[0,1,4][cycle%3]. No three-objective bounds existed',
        oldDemand='Only chose a factory for makespan local search using the latest tight cap and retained-pool minimum C; did not alter donor acceptance',
        sourceAcceptance='Compare all paid rows excluding elapsed time, all available stage population/selection/admission records, common FE checkpoint fronts, initial vectors, and the full captured mature global genomes against frozen original prefix',
        limits='No mainline modification, no new instance or seed, no full algorithm/TIME/NSGA competitiveness claim, no Goal',
        failures='Retain logs and paid costs; no replacement seed or outcome-based retries')
    write(root / 'source-protocol.json', value)
    write(root / 'environment.json', dict(java=subprocess.check_output([str(JAVA), '-version'], stderr=subprocess.STDOUT, text=True),
        javac=subprocess.check_output([str(JAVAC), '-version'], text=True),
        sourceAcceptanceSHA256=sha(SOURCE / 'delivery-acceptance.json'),
        anchorAcceptanceSHA256=sha(ANCHOR / 'delivery-acceptance.json')))
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(freeze(args.root)['sourceAdditionalAttemptedFE'])
