"""Trace all existing production candidates and preserve every A0-novel witness."""
import argparse
from collections import Counter
import json
from pathlib import Path
import time
import numpy as np
from common import RUN, SOURCE, MATURE, STEMS, SEEDS, ARMS, FACTORY, prepare, read, write, rows, identity
from features import describe, weakly_covered, physical_signature, summarize_features


def trace(folder, background):
    before = read(folder / 'before.json')
    live = {r['slot']: r for r in before}
    ancestors = {r['slot']: [] for r in before}
    catalog = read(folder / 'domain.json')['catalog']
    final = {tuple(v) for v in read(folder / 'front.json')}
    allrows, witnesses, paths = [], [], []
    seen = set()
    steps = iter(rows(folder / 'steps.jsonl'))
    for paid in rows(folder / 'paid.jsonl'):
        if paid['fe'] == 4096:
            terminal = paid
            continue
        step = next(steps)
        parent = live[step['slot']]
        assert step['parentObjectives'] == parent['objectives'] and step['fe'] == paid['fe']
        assert step['objectives'] == paid['objectives']
        signature = physical_signature(paid)
        meta = describe(parent, paid, catalog)
        novel = not weakly_covered(background, paid['objectives'])
        record = dict(fe=paid['fe'], role=paid['role'], slot=paid['slot'], parentId=paid['parentId'],
                      accepted=step['accepted'], fresh=paid['fresh'], a0Novel=novel,
                      finalSurvivor=tuple(paid['objectives']) in final, physicalFirstSeen=signature not in seen,
                      parentCoveredByA0=weakly_covered(background, parent['objectives']),
                      ancestry=list(ancestors[step['slot']]), **meta)
        allrows.append(record)
        if novel:
            witnesses.append(dict(record=record, parent=parent, candidate=paid, step=step))
        seen.add(signature)
        if step['accepted']:
            ancestors[step['slot']].append(paid['fe'])
            live[step['slot']] = paid
    assert len(allrows) == 4095 and next(steps, None) is None
    for r in read(folder / 'after.json'):
        assert r['objectives'] == live[r['slot']]['objectives']
    groups = {label: summarize_features([r for r in allrows if check(r)]) for label, check in (
        ('all', lambda r: True), ('positiveA0', lambda r: r['a0Novel']),
        ('negativeA0', lambda r: not r['a0Novel']), ('accepted', lambda r: r['accepted']),
        ('newFinal', lambda r: r['a0Novel'] and r['finalSurvivor']))}
    entries = [dict(slot=r['slot'], role=r['role'], objectives=r['objectives'],
                    coveredByA0=weakly_covered(background, r['objectives']),
                    coveringA0Points=int(np.sum(np.all(background <= r['objectives'], axis=1))),
                    **{k:r[k] for k in FACTORY}) for r in before]
    return dict(groups=groups, entry=entries, uniquePhysical=len(seen),
                terminalNovel=not weakly_covered(background, terminal['objectives']),
                terminalObjectives=terminal['objectives']), allrows, witnesses


def main(output):
    prepare()
    assert not output.exists(), 'Never overwrite prior analysis'
    output.mkdir(parents=True)
    start = time.perf_counter()
    cases, sources = [], []
    for stem in STEMS:
        for seed in SEEDS:
            background_path = SOURCE / 'inputs-v2' / stem / str(seed) / '0/background.json'
            background = np.asarray(read(background_path), dtype=float)
            sources.append(background_path)
            for arm in ARMS:
                folder = RUN / 'science' / stem / str(seed) / arm
                sources.extend(folder / name for name in ('before.json','after.json','domain.json','paid.jsonl','steps.jsonl','front.json'))
                result, features, witnesses = trace(folder, background)
                case = dict(instance=stem, seed=seed, arm=arm, **result)
                cases.append(case)
                name = f'{stem}-{seed}-{arm}'
                write(output / (name + '-witnesses.json'), witnesses)
                with (output / (name + '-features.jsonl')).open('x', encoding='utf-8') as stream:
                    for r in features:
                        stream.write(json.dumps(r, separators=(',', ':')) + '\n')
                print('TRACE', name, result['groups']['positiveA0'], flush=True)
    write(output / 'input-identity.json', identity(sources))
    write(output / 'survey.json', dict(cases=cases, scientificFEAdded=0, decoderCalls=0,
          candidateRows=18*4095, terminalRows=18, seconds=time.perf_counter()-start,
          scope='Retrospective labels only; A0-novel is not a causal or material improvement claim'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args().output)
