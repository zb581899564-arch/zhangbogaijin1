"""Freeze sources, recipients, ordinary proposals and a 60+4 budget before decoding."""
import argparse
from pathlib import Path
from transfer_common import *
from transfer_edits import apply_source, changes, displacement, ordinary


def original_file(path, frozen_root, identities):
    digest = sha(path)
    assert digest == read(frozen_root / 'delivery-manifest.json')[str(path.relative_to(frozen_root))]
    identities[str(path)] = digest


def load_sources(identities):
    report_path = CF / 'analysis/report.json'
    original_file(report_path, CF, identities)
    results = {c['id']: c for c in read(report_path)['cases']}
    selected = {cid for cid, c in results.items()
                if c['label'] == 'POSITIVE' and c['classification']['strictBetterNewPhysicalSubsets']}
    assert selected == set(SOURCE_MASKS)
    sources = []
    for cid, mask in SOURCE_MASKS.items():
        candidates = results[cid]['classification']['strictBetterNewPhysicalSubsets']
        assert mask == min(candidates, key=lambda m: (m.bit_count(), m))
        path = CF / 'cases' / (cid + '.json')
        original_file(path, CF, identities)
        source = read(path)
        source['prunedMask'] = mask
        source['fullMask'] = sum((1 << i) for i, job in enumerate(source['jobs'])
            if source['parent']['resources'][job] != source['child']['resources'][job])
        source['fullMask'] += sum((1 << (i + 2)) for i, job in enumerate(source['jobs'])
            if source['parent']['keys'][job] != source['child']['keys'][job])
        assert source['fullMask'] & mask == mask
        source['prunedObjectives'] = results[cid]['objectives'][mask]
        assert source['instance'] == STEM and source['seed'] == SEED
        transferred = apply_source(source['parent'], source, mask)
        for field in (*FIELDS, 'resources', 'keys'):
            assert transferred[field] == source['variants'][mask][field]
        sources.append(source)
    assert all(s['catalog'] == sources[0]['catalog'] for s in sources)
    assert all(s['A0'] == sources[0]['A0'] for s in sources)
    return sources


def recipients(sources, identities):
    excluded = set()
    for source in sources:
        excluded.update((physical(source['parent']), physical(source['child']),
                         physical(apply_source(source['parent'], source, source['prunedMask']))))
    by_seed, eligible = {}, []
    for seed in (16110003, SEED, 16110069):
        path = OLD / 'science' / STEM / str(seed) / 'LEGAL/before.json'
        original_file(path, OLD, identities)
        records = read(path)
        same_fa = [p for p in records if all(fa_map(p) == fa_map(s['parent']) for s in sources)]
        by_seed[str(seed)] = dict(total=len(records), exactFACompatible=len(same_fa))
        if seed != SEED:
            assert not same_fa, 'Different eligibility requires an amendment before querying'
            continue
        seen = set()
        for p in sorted(same_fa, key=lambda row: row['slot']):
            signature = physical(p)
            if signature in excluded or signature in seen:
                continue
            seen.add(signature)
            eligible.append(dict(p, id=f"receiver-{p['slot']:03d}"))
    assert len(eligible) == 4
    assert {p['role'] for p in eligible} == {'MAKESPAN', 'CENTER', 'ENERGY', 'WORKER_COST'}
    return eligible, by_seed


def build_queries(sources, receivers):
    result = []
    for source in sources:
        for receiver in receivers:
            full = apply_source(receiver, source, source['fullMask'])
            pruned = apply_source(receiver, source, source['prunedMask'])
            children = [('FULL', full, None), ('PRUNED', pruned, None)]
            children.extend((f'RANDOM_{i}', *ordinary(receiver, pruned, source, i)) for i in range(3))
            for arm, child, rng_seed in children:
                assert fa_map(child) == fa_map(receiver)
                assert all(0 <= r < len(source['catalog']) for r in child['resources'])
                assert all(0 <= k <= 1 for k in child['keys'])
                result.append(dict(child, id=f"{source['id']}/{receiver['id']}/{arm}",
                    source=source['id'], receiver=receiver['id'], arm=arm,
                    sourceAtomMask=source['fullMask'] if arm == 'FULL' else source['prunedMask'],
                    randomSeed=rng_seed, changedFields=changes(receiver, child),
                    **displacement(receiver, child)))
    return result


def known_background(sources, identities):
    points = list(sources[0]['A0'])
    for arm in ('LEGAL', 'NOVEL'):
        path = OLD / 'science' / STEM / str(SEED) / arm / 'front.json'
        original_file(path, OLD, identities)
        points.extend(read(path))
    for case in read(CF / 'analysis/report.json')['cases']:
        if (case['instance'], case['seed']) == (STEM, SEED):
            points.extend(case['objectives'])
    from research.dynamic_benchmark.metrics import nondominated
    return nondominated(points).tolist()


def amendment_evidence(receivers, queries, identities):
    previous = BASE / 'runs/linux-edit-transfer-20261106-01'
    assert not (previous / 'qa').exists() and not (previous / 'paid').exists()
    assert read(previous / 'receivers.json') == receivers
    old = {q['id']: q for q in read(previous / 'queries.json')}
    unchanged = 0
    for query in queries:
        if query['arm'] != 'FULL':
            assert query == old[query['id']]
            unchanged += 1
    for name in ('protocol.json', 'receivers.json', 'queries.json', 'STOP_BEFORE_EVALUATION.json'):
        path = previous / name
        identities[str(path)] = sha(path)
    assert unchanged == 48
    return dict(previousPaidFE=0, previousQA=0, recipientsExactlyUnchanged=True,
                unchangedPrunedAndOrdinaryQueries=unchanged, sourceInactiveFieldsExcluded=True)


def main(root):
    prepare()
    assert not (root / 'input-identity.json').exists(), 'Never overwrite a frozen run'
    identities = {}
    sources = load_sources(identities)
    receivers, eligibility = recipients(sources, identities)
    queries = build_queries(sources, receivers)
    assert len(queries) == 60
    known = known_background(sources, identities)
    amendment = amendment_evidence(receivers, queries, identities)
    for name in ('protocol.json', 'paid-independent-audit.json', 'qa-independent-audit.json',
                 'build-01/identity.json', 'build-01/classpath.txt'):
        p = CF / name
        original_file(p, CF, identities)
    for name in (STEM + '.txt', 'RECONSTRUCTED-setup.txt', 'fatigue-input.txt'):
        p = ANCHOR / 'payload/inputs' / STEM / name
        identities[str(p)] = sha(p)
    for p in [MATURE / 'protocol.json', MATURE / 'analysis-code/analysis_metrics.py',
              OLD / 'analysis-code-v2/volume.py', CF / 'audit-code/audit.py']:
        identities[str(p)] = sha(p)
    for p in sorted(Path(__file__).parent.glob('*.py')):
        identities[str(p)] = sha(p)
    root.mkdir(parents=True, exist_ok=True)
    write(root / 'input-identity.json', identities)
    write(root / 'sources.json', sources)
    write(root / 'receivers.json', receivers)
    write(root / 'queries.json', queries)
    write(root / 'known-background.json', known)
    write(root / 'amendment-evidence.json', amendment)
    write(root / 'eligibility.json', dict(bySeed=eligibility, recipients=[
        dict(id=p['id'], slot=p['slot'], role=p['role'], stateId=p['stateId']) for p in receivers],
        exactWholeFA=True, originalParentChildPrunedExcluded=True, selectionUsedObjectives=False))
    write(root / 'protocol.json', dict(version='EDIT_TRANSFER_V2', instance=STEM, seed=SEED,
        sources=SOURCE_MASKS, arms=list(ARMS), receiverCount=4, blocks=12,
        fullSourceMasks={s['id']: s['fullMask'] for s in sources},
        amendment='V1 frozen before any QA or paid decode, stopped: source-inactive fields must not become new edits on recipients. Same recipients, budget and random streams.',
        supersedes=str(BASE / 'runs/linux-edit-transfer-20261106-01'),
        plannedNewEvaluations=60, plannedQA=4, hardLimitFE=60, hardLimitQA=4,
        transfer='Copy exact child values only on source-active fields; no adaptation, repair or transfer of source-inactive fields',
        controls='3 separately reported ordinary streams; same jobs, field types and actual replaced field counts as PRUNED',
        controlLimitation='Order displacement is recorded, not forced equal; neutral/duplicate proposals are charged without redraw',
        transportMask='Frozen evaluator uses QA=0, PAID=1 only as row tags; sourceAtomMask is in queries.json',
        referenceRule='ND(A0 plus all 60 new candidates); common offline reference for all arms and slices',
        additionalBackground='Known-source envelope: A0 + old LEGAL/NOVEL final fronts + all old counterfactual configurations for this source',
        mainMetrics=['HV', 'IGDplus', 'C_A_B', 'C_B_A'], extraMetrics=['IGD', 'complete objective-minimum vectors'],
        hvReferences=[1.5, 1.25, 2.0], hvNumericalAbsTol=1e-12, objectiveCertificateAbsTol=[1e-8]*3,
        structuralGate='At least 2 source edits each strictly dominate FULL on at least 2 of the 4 other physical recipients',
        capacityGate='PRUNED union above A0 >= 0.1% HV, inherited capacity screen, not a journal or algorithm-competition standard',
        comparisonGate='Report FULL and all 3 ordinary streams separately; any >1% HV / >5% IGD+ / >10pp C reverse blocks continuation; no weighted score or vote',
        gainGate='PRUNED must add at least a numerical HV or IGD+ improvement over FULL and every ordinary stream; no best-of-stream oracle',
        noSearchUpdate=True, keepFourRolesAndSharing=True, modifyMainline=False, expand=False,
        independence='All recipients are from one pre-existing family and source seed; not independent seeds or held-out trajectories',
        noAlgorithmClaim=True))
    for name, rows, qa in [('qa', receivers, True), ('paid', queries, False)]:
        with (root / (name + '.tsv')).open('x') as stream:
            stream.write('\n'.join(tsv_row(row, qa) for row in rows) + '\n')
    print('FROZEN', len(sources), len(receivers), len(queries), eligibility, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    main(parser.parse_args().root)
