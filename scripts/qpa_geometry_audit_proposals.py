"""Read every case; independently rebuild only the prospectively fixed verification sample."""
from collections import Counter, defaultdict
import csv

from qgomea_reference_math import inverse, order_mix, position_mix
from qpa_geometry_audit_inputs import JavaRandom, physical_hash


def rebuild(points, genes, catalog, pair, mask, kind, reference):
    parent, donor = (points[i] for i in pair)
    lookup = {j: (f, m, w) for j, f, m, w in zip(parent['JS'], parent['FA'], parent['MA'], parent['WA'])}
    other = {j: (f, m, w) for j, f, m, w in zip(donor['JS'], donor['FA'], donor['MA'], donor['WA'])}
    for job in mask:
        lookup[job] = other[job]
    fallback = len({value[0] for value in lookup.values()}) != catalog['factories']
    if fallback:
        return physical_hash(parent, catalog['factories']), True
    if kind == 'PA':
        a, b = (genes[i] for i in pair)
        keys = a['keys'].copy()
        resources = a['resources'].copy()
        for j in mask:
            keys[j], resources[j] = b['keys'][j], b['resources'][j]
        order = sorted(range(len(keys)), key=lambda j: (keys[j], -j))
        assert all(lookup[j] == tuple(catalog['tuples'][resources[j]]) for j in order)
    else:
        a, b = inverse(parent['JS']), inverse(donor['JS'])
        positions = position_mix(a, b, mask, reference)[0] if kind == 'POSITION' else order_mix(a, b, mask)
        order = inverse(positions)
    result = dict(JS=order, **{name: [lookup[j][k] for j in order] for k, name in enumerate(('FA', 'MA', 'WA'))})
    return physical_hash(result, catalog['factories']), False


def check_proposals(root, stem, data, models, catalog, plan, execution, audit_plan):
    original = {}
    counts = defaultdict(Counter)
    sample_count = total = 0
    grouped = list(data)
    with (root/stem/'proposal-hashes.tsv').open(encoding='utf-8') as stream:
        source = iter(csv.DictReader(stream, delimiter='\t'))
        for population, variant in grouped:
            masks = models[population, 'ORIGINAL']['qpaActiveSubsets']
            rng = JavaRandom(execution['referenceSeed'])
            block_size = len(plan['fixedPairs']) * len(masks) * 3
            offset = 0
            for pair_index, pair in enumerate(plan['fixedPairs']):
                for mask_index, mask in enumerate(masks):
                    ref = mask[rng.integer(len(mask))]
                    for kind in ('POSITION', 'ORDER', 'PA'):
                        row = next(source)
                        expected = (population, variant, str(pair_index), str(mask_index), kind, str(ref if kind == 'POSITION' else -1))
                        assert tuple(row[k] for k in ('population', 'variant', 'pair', 'mask', 'kind', 'reference')) == expected
                        total += 1
                        offset += 1
                        assert row['fallback'] in ('true', 'false') and len(row['physicalSHA256']) == 64
                        key = population, pair_index, mask_index, kind
                        if variant == 'ORIGINAL':
                            original[key] = row
                        else:
                            baseline = original[key]
                            assert row['fallback'] == baseline['fallback'] and row['reference'] == baseline['reference']
                            prefix = 'pa' if kind == 'PA' else 'qpa'
                            group = counts[population, variant]
                            group[prefix+'Proposals'] += 1
                            group[prefix+'PhysicalChanged'] += row['physicalSHA256'] != baseline['physicalSHA256']
                            group[prefix+'Fallback'] += row['fallback'] == 'true'
                            if kind == 'PA':
                                assert row['physicalSHA256'] == baseline['physicalSHA256']
                        if total % audit_plan['systematicEveryRows'] == 0 or offset in (1, block_size):
                            assert sample_count < audit_plan['maximumVerificationConstructions']
                            sha, fallback = rebuild(data[population, variant], models[population, variant]['paGenes'],
                                                    catalog, pair, mask, kind, ref)
                            assert sha == row['physicalSHA256'] and fallback == (row['fallback'] == 'true')
                            sample_count += 1
            assert offset == block_size
        assert next(source, None) is None
    return dict(rows=total, verificationConstructions=sample_count), counts
