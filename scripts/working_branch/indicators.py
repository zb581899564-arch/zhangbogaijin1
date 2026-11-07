"""Frozen indicators with independent numerical checks and explicit pairwise directions."""
import numpy as np
import moocore
from common import *


def independent_module():
    path = ANCHOR/'research/dynamic_benchmark/metrics.py'
    if not path.exists():
        path = ANCHOR/'python/research/dynamic_benchmark/metrics.py'
    assert path.exists(), str(path)
    spec = importlib.util.spec_from_file_location('independent_working_metrics', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module, path


def fixtures():
    assert metrics([[.2]*3], [[.3]*3], [1]*3)['IGDplus'] == 0
    assert abs(metrics([[.4]*3], [[.3]*3], [1]*3)['IGDplus']-np.sqrt(.03)) < 1e-14
    assert coverage([[1, 1, 1]], [[1, 1, 1]]) == {'covered': 1, 'denominator': 1, 'C': 1.}
    assert coverage([[0, 2, 1]], [[2, 0, 1]])['covered'] == 0
    assert coverage([[2, 0, 1]], [[0, 2, 1]])['covered'] == 0
    assert keep_fixture()


def keep_fixture():
    from audit_inputs import keep
    return (not keep('MAKESPAN', [1, 0, 0], [1, 2, 2], False)
            and keep('CENTER', [1, 1, 1], [1, 1, 1], True)
            and not keep('CENTER', [2, 1, 1], [1, 1, 1], True))


def measured(front, reference, independent):
    values = metrics(front, reference, SCALE)
    scaled, ref = np.asarray(front)/SCALE, np.asarray(reference)/SCALE
    for point in (1.25, 1.5, 2.0):
        value = float(moocore.hypervolume(scaled, ref=[point]*3))
        assert abs(value-independent.hypervolume(scaled, [point]*3)) < 1e-11
        values['HV'+str(point)] = value
    assert abs(values['IGDplus']-independent.igd_plus(scaled, ref)) < 1e-14
    distance = sum(min(sum((x-y)**2 for x, y in zip(a, r))**.5 for a in scaled) for r in ref)/len(ref)
    assert abs(values['IGD']-distance) < 1e-14
    assert values['HV'] == values['HV1.5']
    return values


def symmetric_improvement(candidate, control):
    return 200*(control-candidate)/(control+candidate) if control+candidate else 0.


def pair(kind, context, control, fronts, values):
    b, c = fronts[kind, context, 'BRANCH'], fronts[kind, context, control]
    bm, cm = values[kind, context, 'BRANCH'], values[kind, context, control]
    bc, cb = coverage(b, c), coverage(c, b)
    for left, right, result in ((b, c, bc), (c, b, cb)):
        count = sum(any(all(x <= y for x, y in zip(p, q)) for p in left) for q in right)
        assert count == result['covered'] and len(right) == result['denominator']
    row = dict(kind=kind, context=context, candidate='BRANCH', control=control,
               HVpct=100*(bm['HV']/cm['HV']-1), IGDplusSymPct=symmetric_improvement(bm['IGDplus'], cm['IGDplus']),
               IGDSymPct=symmetric_improvement(bm['IGD'], cm['IGD']),
               C_BC=bc['C'], C_BC_covered=bc['covered'], C_BC_denominator=bc['denominator'],
               C_CB=cb['C'], C_CB_covered=cb['covered'], C_CB_denominator=cb['denominator'],
               CdiffPP=100*(bc['C']-cb['C']))
    for point in (1.25, 2.0):
        row['HVpct'+str(point)] = 100*(bm['HV'+str(point)]/cm['HV'+str(point)]-1)
    row['signal'] = row['HVpct'] >= .1 or row['IGDplusSymPct'] >= 5
    row['majorReverse'] = row['HVpct'] < -.1 or row['IGDplusSymPct'] < -5 or row['CdiffPP'] < -10
    row['HVreferenceFlip'] = any(row['HVpct']*row['HVpct'+str(p)] < -1e-16 for p in (1.25, 2.0))
    return row
