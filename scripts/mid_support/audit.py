"""Independent intervention and timeline audit, with zero new decoder queries."""
import argparse
import importlib.util
from collections import Counter
from urllib.parse import urlparse, unquote
import numpy as np
from common import *


def verify_classes(root, loaded):
    identity = read(root/'build/identity.json')
    checks = 0
    for name, meta in loaded.items():
        if not isinstance(meta, dict):
            continue
        resource = meta['resource']
        assert resource.startswith('file:'), resource
        path = Path(unquote(urlparse(resource).path))
        own = root/'build/classes'
        expected = identity['classes'].get(str(path.relative_to(own))) if path.is_relative_to(own) else None
        if expected is None:
            for base, items in identity['dependencies'].items():
                if isinstance(items, dict) and path.is_relative_to(Path(base)):
                    expected = items[str(path.relative_to(Path(base)))];break
        assert expected is not None and sha(path) == meta['sha256'] == expected, name
        checks += 1
    return checks


def intervention(root):
    entries = {s['id']: s for s in read(root/'prepared/entries.json')}
    tables = {s['context']: {t['receiverFreeIndex']: t for t in s['tables']}
              for s in read(root/'prepared/shuffle-tables.json')}
    catalog = read(root/'sources/models.json')['catalog']
    queries = {q['id']: q for q in stream(root/'prepared/queries.jsonl')}
    models = {m['context']: m for m in read(root/'sources/models.json')['models']}
    count, marginal_checks = 0, 0
    for context, entry in entries.items():
        free = [p for p in entry['S'] if p['family'] == -1]
        pa = [entry['PA'][int((i+0.5)*100/80)] for i in range(80)]
        for index, table in tables[context].items():
            eligible = [i for i in range(80) if i != index]
            for job in range(100):
                assert Counter(pa[i]['resources'][job] for i in eligible) == Counter(table['resources'][i][job] for i in eligible)
                marginal_checks += 1
        schedule = [s for s in stream(root/'prepared/schedule.jsonl') if s['context'] == context]
        assert len(schedule) == 512 and Counter(s['role'] for s in schedule) == dict.fromkeys(ROLES, 128)
        for s in schedule:
            i, d, mask = s['receiverFreeIndex'], s['donorIndex'], set(s['mask'])
            assert i != d and s['mask'] == models[context]['subsets'][s['maskIndex']]
            parent, donor = free[i], free[d]
            assert parent['slot'] == s['receiverSlot'] and parent['family'] == -1
            for arm, supplied in zip(ARMS, (donor['resources'], pa[d]['resources'], tables[context][i]['resources'][d])):
                q = queries[s['id']+'-'+arm]
                expected_r = [supplied[j] if j in mask else parent['resources'][j] for j in range(100)]
                expected_k = [donor['keys'][j] if j in mask else parent['keys'][j] for j in range(100)]
                fallback = len({catalog[r][0] for r in expected_r}) != max(t[0] for t in catalog)+1
                if fallback:
                    expected_r, expected_k = parent['resources'], parent['keys']
                assert q['fallback'] == fallback and q['resources'] == expected_r and q['keys'] == expected_k
                for name, values in encode(expected_r, expected_k, catalog).items():
                    assert q[name] == values
                count += 1
    assert count == len(queries) == 4608
    return queries, marginal_checks


def main(root):
    assert read(root/'accounting.json')['passed']
    queries, marginals = intervention(root)
    expected = {'paid': queries, 'qa': {r['id']: r for r in stream(root/'prepared/qa.jsonl')}}
    # Reuse the prior accepted independent timeline checker, not the decoder itself.
    old_audit = BASE/'runs/linux-counterfactual-edit-20261106-01/audit-code/audit.py'
    assert old_audit.is_file()
    sys.path.insert(0, str(old_audit.parent))
    spec = importlib.util.spec_from_file_location('legacy_timeline_audit', old_audit)
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    operations = classes = checked = 0;maximum = 0.;physical_seen = {}
    for kind in ('qa', 'paid'):
        seen = set()
        for folder in sorted((root/kind).iterdir()):
            receipt = read(folder/'receipt.json');classes += verify_classes(root, receipt['loaded'])
            for number, row in enumerate(stream(folder/'evaluations.jsonl'), 1):
                assert row['number'] == number and row['id'] not in seen
                frozen = expected[kind][row['id']]
                assert all(row[f] == frozen[f] for f in (*FIELDS, 'resources', 'keys'))
                if kind == 'qa':
                    assert row['objectives'] == frozen['objectives']
                count, error = module.timeline(row)
                operations += count;maximum = max(maximum, error);checked += 1;seen.add(row['id'])
                signature = physical(row)
                if signature in physical_seen:
                    assert physical_seen[signature] == row['objectives']
                physical_seen[signature] = row['objectives']
        assert seen == set(expected[kind])
    assert checked == 5208
    verify_classes(root, read(root/'sources/models.json')['loaded'])
    write(root/'independent-audit.json', dict(passed=True, candidateRows=4608, qaRows=600,
          checkedOperations=operations, loadedClassChecks=classes, maxObjectiveAggregationError=maximum,
          perJobShuffledMarginalChecks=marginals, allMatchedInterventions=True,
          nativeGeneratorGate=read(root/'native-gate.json'), priorTimelineAuditSource=str(old_audit),
          priorTimelineAuditSHA256=sha(old_audit), frozenInputHashes={p:sha(p) for p in input_args()},
          distinctPhysicalSchedules=len(physical_seen), newDecoderCalls=0))
    print('INDEPENDENT_AUDIT_PASSED', checked, 'rows', operations, 'operations', flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root', type=Path);args=p.parse_args();linux();main(args.root)
