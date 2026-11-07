"""Independent vectorized job-index oracle for native copy/fallback and actual family projection."""
import numpy as np


def by_job(point):
    n = len(point['JS']); result = np.empty((n, 3), dtype=np.int64)
    result[np.array(point['JS'])] = np.array([point['FA'], point['MA'], point['WA']]).T
    return result


def analyze(points, receipt):
    sources = np.array([by_job(p) for p in points]); pcount, n, _ = sources.shape; assert pcount == 100
    factories = receipt['factories']; machines = np.array(receipt['machineCounts']); workers = np.array(receipt['workerCounts'])
    cells = {}; compatible = 0
    for parent in range(100):
        p = sources[parent]
        for donor in range(100):
            d = sources[donor]
            pc, dc = ('FIXED' if parent < 20 else 'FREE'), ('FIXED' if donor < 20 else 'FREE')
            if parent >= 20:
                key = pc+'/'+dc+'/FULL'; value = cells.setdefault(key, np.zeros(7, dtype=np.int64)); value[0] += 1
                continue
            compatible += np.array_equal(p[:, 0], d[:, 0])
            before = np.repeat(p[None, :, :], n+1, axis=0)
            before[np.arange(n), np.arange(n)] = d; before[-1] = d
            missing = np.zeros(n+1, bool)
            for f in range(factories):
                missing |= ~np.any(before[:, :, 0] == f, axis=1)
            before[missing] = p
            after = before.copy(); after[:, :, 0] = p[:, 0]
            after[:, :, 1] %= machines[p[:, 0]]; after[:, :, 2] %= workers[p[:, 0]]
            changed = np.any(after != before, axis=2)
            third = changed & np.any(after != p, axis=2) & np.any(after != d, axis=2)
            for kind, indices in (('SINGLE', slice(0, n)), ('FULL', slice(n, n+1))):
                raw, projected = before[indices], after[indices]
                delta = np.array([len(raw), missing[indices].sum(), np.any(changed[indices], axis=1).sum(),
                    (raw[:, :, 0] != projected[:, :, 0]).sum(), (raw[:, :, 1] != projected[:, :, 1]).sum(),
                    (raw[:, :, 2] != projected[:, :, 2]).sum(), third[indices].sum()], dtype=np.int64)
                key = pc+'/'+dc+'/'+kind; cells.setdefault(key, np.zeros(7, dtype=np.int64))[:] += delta
    expected = {k: v.tolist() for k, v in cells.items()}
    assert expected == receipt['cells'], (expected, receipt['cells'])
    assert compatible == receipt['fullFACompatiblePairs'] and receipt['fixedParentDonorPairs'] == 2000
    assert receipt['knownPaidSources'] == 100 and receipt['newSearchFE'] == receipt['decoderCalls'] == 0
    for witness in receipt['witnesses']:
        p, d, job = witness['parent'], witness['donor'], witness['job']
        original, incoming = sources[p, job], sources[d, job]
        expected_after = [int(original[0]), int(incoming[1] % machines[original[0]]), int(incoming[2] % workers[original[0]])]
        assert witness['parentTuple'] == original.tolist() and witness['donorTuple'] == witness['nativeTuple'] == incoming.tolist()
        assert witness['afterGuard'] == expected_after
    return {'independentIntegerCountsExact': True, 'fixtures': sum(v[0] for v in expected.values()),
            'fixedProjectionChanged': sum(v[2] for k, v in expected.items() if k.startswith('FIXED/')),
            'fixedFixtures': sum(v[0] for k, v in expected.items() if k.startswith('FIXED/')),
            'projectedThirdTupleJobs': sum(v[6] for v in expected.values()),
            'nativeFallbacks': sum(v[1] for v in expected.values()), 'compatibleWholeFA': compatible,
            'fixedDonorPairs': 2000, 'newSearchFE': 0, 'decoderCalls': 0}
