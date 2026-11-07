"""Read-only checks on temporal archives, matched cases and neutral encodings."""
from collections import Counter
import numpy as np
from cf_common import physical, read, write


def verify_cases(root, cases, matrices):
    protocol = read(root / 'protocol.json')
    assert not protocol['missing']
    labels = Counter(c['label'] for c in cases.values())
    assert labels == dict(POSITIVE=8, MATCHED_NEGATIVE=8, BACKGROUND_NEGATIVE=10)
    matched = neutral = 0
    for case in cases.values():
        before = np.asarray(case['beforeEvent'])
        step = case['step']
        assert len(before) == step['archiveBefore'], case['id']
        fresh = not np.any(np.all(before <= case['child']['objectives'], axis=1))
        assert bool(fresh) == step['fresh'], case['id']
        if case['label'] == 'POSITIVE':
            assert fresh
        else:
            assert np.any(np.all(np.asarray(case['A0']) <= case['child']['objectives'], axis=1))
        if case['label'] == 'MATCHED_NEGATIVE':
            positive = cases[case['matchedPositive']]
            assert (case['instance'], case['seed'], case['arm']) == (
                positive['instance'], positive['seed'], positive['arm'])
            assert step['parentId'] == positive['step']['parentId']
            assert physical(case['parent']) == physical(positive['parent'])
            assert case['child']['generation']['factory'] == positive['child']['generation']['factory']
            matched += 1
        seen = {}
        for row in matrices[case['id']]:
            signature = physical(row)
            if signature in seen:
                assert row['objectives'] == seen[signature], (case['id'], row['mask'])
                neutral += 1
            else:
                seen[signature] = row['objectives']
    result = dict(passed=True, cases=len(cases), labelCounts=dict(labels),
                  matchedSamePhysicalParentAndFactory=matched,
                  repeatedPhysicalRowsExactObjectiveMatches=neutral,
                  eventArchiveSizesAndFreshStatusChecked=len(cases),
                  originalPriorFEOnly=True, newDecoderCalls=0)
    write(root / 'analysis' / 'evidence-audit.json', result)
    return result
