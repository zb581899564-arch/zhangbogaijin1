"""Select time-locked source entries and archives, without objective-based resampling."""
import argparse
import csv
from common import *


def share_sources(root):
    populations, workspaces, roles = {}, {}, {}
    for r in stream(root/'historical-share/pipeline.jsonl'):
        if r['kind'] == 'population' and r['phase'] == 'POST_GLOBAL':
            populations[r['fe']] = r
        if r['kind'] == 'workspace':
            workspaces[r['fe']] = r
        if r['kind'] == 'program':
            assert r['slot'] not in roles or roles[r['slot']] == r['preference']
            roles[r['slot']] = r['preference']
    expected = ['MAKESPAN']*15+['CENTER']*55+['ENERGY']*15+['WORKER_COST']*15
    assert [roles[i] for i in range(100)] == expected
    times = [min(t for t in populations if t >= 100000), min(t for t in populations if t >= 175000),
             max(t for t in populations if t <= 250000)]
    assert len(set(times)) == 3
    old = {r['fe']: r for r in stream(OLD/'capture/SHARE_CTX_GOM/trajectory-events.jsonl')
           if r['kind'] == 'population' and r['label'] == 'POST_GLOBAL' and r['fe'] in times}
    output = []
    for t in times:
        population, workspace = populations[t], workspaces[t]
        assert len(population['points']) == len(workspace['states']) == 100
        for i, (p, w, frozen) in enumerate(zip(population['points'], workspace['states'], old[t]['points'])):
            assert w['sourceKey'] == p['key'] == frozen['key']
            assert p['objectives'] == w['objectives'] == frozen['objectives']
            # The newer read-only trace uses null for the same unrestricted family (-1).
            trace_family = -1 if frozen['family'] is None else frozen['family']
            assert p['family'] == w['family'] == trace_family
        points = [dict(w, slot=i, role=roles[i], original=p) for i, (w, p) in
                  enumerate(zip(workspace['states'], population['points']))]
        output.append(dict(id=str(t), fe=t, cycle=population['cycle'], S=points))
    return output


def archives(arm, times):
    admitted, output = [], {}
    with (OLD/'capture'/arm/'trajectory-paid.csv').open() as f:
        for r in csv.DictReader(f):
            fe = int(r['fe'])
            if fe > max(times):
                break
            if r['admitted'] == '1':
                admitted.append([float(r[k]) for k in ('Cmax', 'TEC', 'TWC')])
            if fe in times:
                output[fe] = nd(admitted).tolist()
    assert set(output) == set(times)
    return output


def main(root):
    assert read(root/'source-gate.json')['passed']
    selected = share_sources(root)
    models = rows(root/'pa-source/models.jsonl')
    events = [r for r in stream(root/'pa-source/trajectory-events.jsonl')
              if r['kind'] == 'population' and r['label'] == 'PA_MODEL']
    assert len(models) == len(events)
    for i, (m, e) in enumerate(zip(models, events), 1):
        assert m['model'] == i and len(m['points']) == 100
        assert [p['objectives'] for p in m['points']] == [p['objectives'] for p in e['points']]
        m['fe'] = e['fe']
        assert max(p['paidFE'] for p in m['points']) <= m['fe']
    times = [s['fe'] for s in selected]
    sa, pa = archives('SHARE_CTX_GOM', times), archives('PA_JOINT', times)
    free = []
    for s in selected:
        model = max((m for m in models if m['fe'] <= s['fe']), key=lambda m: m['fe'])
        s.update(PA=model['points'], paModelFE=model['fe'], paModelOrdinal=model['model'],
                 S_archive=sa[s['fe']], PA_archive=pa[s['fe']], A0=nd(sa[s['fe']]+pa[s['fe']]).tolist())
        members = [p for p in s['S'] if p['family'] == -1]
        assert len(members) == 80
        free.extend('\t'.join([s['id'], csv_value(p['resources']), csv_value(p['keys'])]) for p in members)
    target = root/'sources';target.mkdir()
    write(target/'entries.json', selected)
    (target/'free80.tsv').write_text('\n'.join(free)+'\n')
    execute(java(root, 'research.dynamic.SupportModels')+input_args()[:2]+
            [str(target/'free80.tsv'), str(target/'models.json')], root/'model-fixture')
    print('SOURCE_ENTRIES', [(s['fe'], s['paModelFE']) for s in selected], flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root', type=Path);args=p.parse_args();linux();main(args.root)
