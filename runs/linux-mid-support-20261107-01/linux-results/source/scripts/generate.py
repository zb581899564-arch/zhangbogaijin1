"""Fixed-parent, fixed-key, fixed-FOS resource supply intervention; never decodes."""
import argparse
from collections import Counter
import hashlib
import random
import numpy as np
from common import *


def rng(context, slot, label):
    text = f'mid-support-v1|{SEED}|{context}|{slot}|{label}'
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], 'big'))


def verify_models(root, entries, model_data):
    sys.path.insert(0, str(root/'source/audit'))
    from audit_models import expected_matrix, hierarchy
    errors = []
    catalog = model_data['catalog']
    for entry, model in zip(entries, model_data['models']):
        assert entry['id'] == model['context']
        free = [p for p in entry['S'] if p['family'] == -1]
        fa = np.array([[catalog[r][0] for r in p['resources']] for p in free])
        keys = np.array([p['keys'] for p in free])
        expected = expected_matrix(fa, keys, model_data['factories'])
        error = float(np.max(np.abs(expected-np.array(model['dependency']))))
        assert error < 3e-12
        errors.append(dict(context=entry['id'], maxDependencyError=error,
                           maxMergeDeficit=hierarchy(expected, model['subsets'])))
    return errors


def source_rows(entries, catalog):
    qa = []
    for entry in entries:
        for label in ('S', 'PA'):
            for i, p in enumerate(entry[label]):
                encoded = encode(p['resources'], p['keys'], catalog)
                original = p['original'] if label == 'S' else p
                before = dict(original, resources=p['resources'])
                assert physical(before) == physical(dict(p, **encoded))
                p.update(encoded)
                qa.append(dict(p, id=f"{entry['id']}-{label}-{i}"))
    return qa


def pool_for_receiver(pa, slot, context):
    eligible = [i for i in range(80) if i != slot]
    shuffled = [p['resources'][:] for p in pa]
    generator = rng(context, slot, 'per-job-permutation')
    for job in range(100):
        incoming = [pa[i]['resources'][job] for i in eligible]
        generator.shuffle(incoming)
        for i, value in zip(eligible, incoming):
            shuffled[i][job] = value
        assert Counter(incoming) == Counter(pa[i]['resources'][job] for i in eligible)
    return eligible, shuffled


def child(parent, donor_resources, donor_keys, mask, catalog):
    resources, keys = parent['resources'][:], parent['keys'][:]
    for j in mask:
        resources[j], keys[j] = donor_resources[j], donor_keys[j]
    fallback = len({catalog[r][0] for r in resources}) != max(t[0] for t in catalog)+1
    if fallback:
        resources, keys = parent['resources'][:], parent['keys'][:]
    return dict(resources=resources, keys=keys, fallback=fallback, **encode(resources, keys, catalog))


def generate_context(entry, model, catalog):
    free = [p for p in entry['S'] if p['family'] == -1]
    pa_slots = [int((i+0.5)*100/80) for i in range(80)]
    pa = [entry['PA'][i] for i in pa_slots]
    receivers = [i for role in ROLES for i in [n for n, p in enumerate(free) if p['role'] == role][:4]]
    assert len(receivers) == 16 and len(set(pa_slots)) == 80
    queries, fixtures, schedule, shuffle_tables = [], [], [], []
    for index in receivers:
        parent = free[index]
        eligible, shuffled = pool_for_receiver(pa, index, entry['id'])
        shuffle_tables.append(dict(receiverFreeIndex=index, excluded=index, resources=shuffled))
        generator = rng(entry['id'], index, 'masks-and-donors')
        masks = generator.sample(range(len(model['subsets'])), 32)
        for step, m in enumerate(masks):
            donor_index = generator.choice(eligible)
            donor, mask = free[donor_index], model['subsets'][m]
            key = f"{entry['id']}-{parent['slot']}-{step}"
            schedule.append(dict(id=key, context=entry['id'], receiverFreeIndex=index, receiverSlot=parent['slot'],
                                 role=parent['role'], maskIndex=m, mask=mask, donorIndex=donor_index,
                                 sourceShareSlot=donor['slot'], sourcePaSlot=pa_slots[donor_index]))
            for arm, resources in zip(ARMS, (donor['resources'], pa[donor_index]['resources'], shuffled[donor_index])):
                row = dict(child(parent, resources, donor['keys'], mask, catalog), id=key+'-'+arm,
                           proposal=key, arm=arm, context=entry['id'], role=parent['role'], receiver=parent['slot'], mask=mask)
                queries.append(row)
                if arm == 'S_RESOURCE':
                    fixtures.append('\t'.join([row['id'], csv_value(parent['resources']), csv_value(parent['keys']),
                      csv_value(donor['resources']), csv_value(donor['keys']), csv_value(mask),
                      csv_value(row['resources']), csv_value(row['keys']), str(row['fallback']).lower()]))
    return queries, fixtures, schedule, shuffle_tables


def support_report(entry):
    s = [p['resources'] for p in entry['S'] if p['family'] == -1]
    pa = [entry['PA'][int((i+0.5)*100/80)]['resources'] for i in range(80)]
    return dict(context=entry['id'], shareFE=entry['fe'], paModelFE=entry['paModelFE'],
      paSourceLagFE=entry['fe']-entry['paModelFE'], jobs=[dict(job=j,
      shareSupport=sorted({r[j] for r in s}), paSupport=sorted({r[j] for r in pa}),
      paAbsentFromShare=sorted({r[j] for r in pa}-{r[j] for r in s})) for j in range(100)])


def main(root):
    entries = read(root/'sources/entries.json');models = read(root/'sources/models.json')
    errors = verify_models(root, entries, models)
    qa = source_rows(entries, models['catalog'])
    queries, fixtures, schedule, shuffles = [], [], [], []
    for e, m in zip(entries, models['models']):
        q, f, s, t = generate_context(e, m, models['catalog'])
        queries.extend(q);fixtures.extend(f);schedule.extend(s);shuffles.append(dict(context=e['id'], tables=t))
    assert len(queries) == 4608 and len(qa) == 600 and len(fixtures) == len(schedule) == 1536
    output = root/'prepared';output.mkdir()
    write(output/'entries.json', entries);write(output/'shuffle-tables.json', shuffles)
    write(output/'support-triage.json', [support_report(e) for e in entries])
    jsonl(output/'queries.jsonl', queries);jsonl(output/'schedule.jsonl', schedule);jsonl(output/'qa.jsonl', qa)
    (output/'native-fixture.tsv').write_text('\n'.join(fixtures)+'\n')
    for kind, data, count in (('qa', qa, 52), ('paid', queries, 364)):
        folder=output/kind;folder.mkdir()
        for begin in range(0, len(data), count):
            (folder/f'{begin//count:03}.tsv').write_text('\n'.join(tsv_row(row, kind=='qa') for row in data[begin:begin+count])+'\n')
    write(output/'generation-gate.json', dict(passed=True, models=errors, generatedCandidates=len(queries),
          sourceQA=len(qa), sameLegalParentKeysMaskAndRow=True, shuffledExactPerJobEligibleMarginals=True,
          newDecodes=0, rngRule='sha256(mid-support-v1|14910003|context|receiverFreeIndex|label) first8 BE -> Python Random',
          legacyEvaluatorMask='1 is transport only; actual FOS in schedule.jsonl',
          sourceHashes={str(p.relative_to(root)): sha(p) for p in (root/'source').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))
    print('PREPARED', len(queries), 'paid', len(qa), 'QA', flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('root', type=Path);args=p.parse_args();linux();main(args.root)
