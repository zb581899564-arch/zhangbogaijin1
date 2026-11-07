"""Independently replay actual archive admissions and HV from every already-paid objective row."""
import csv
import numpy as np

from run_long_budget_bridge import rows, hypervolume
from fa_admission_volume import volume


class PaidArchiveStream:
    def __init__(self, folder, normalization):
        self.stream = (folder / 'program-paid-objectives.csv').open(encoding='utf-8')
        self.records = iter(csv.DictReader(self.stream));self.front = np.empty((0, 3));self.fe = 0
        self.lower = np.asarray(normalization['lower']);self.scale = np.asarray(normalization['scale'])
        self.hv = 0.;self.inside = 0;self.phases = {};self.admissions = 0;self.max_hv_error = 0.
        self.checks = {int(p['checkpoint']): p for p in rows(folder / 'anytime.jsonl')
                       if p['checkpointKind'] == 'FE' and p['reached']}
        self.checked = set()

    def advance(self, target, episode=None, phase=None):
        assert target >= self.fe
        while self.fe < target:
            row = next(self.records);fe = int(row['fe']);assert fe == self.fe + 1
            own = int(row['episode'])
            if episode is not None:assert own == episode and row['phase'] == phase
            elif own != 0:raise AssertionError('Unattributed intra-program paid row')
            if own:self.inside += 1
            self.phases[row['phase']] = self.phases.get(row['phase'], 0) + 1
            point = (np.asarray([float(row[k]) for k in ('C', 'E', 'W')]) - self.lower) / self.scale
            changed = not np.any(np.all(self.front <= point, axis=1))
            assert changed == bool(int(row['archiveChanged'])), 'Recorded archive admission differs'
            if changed:
                self.front = np.vstack([self.front[~np.all(point <= self.front, axis=1)], point])
                updated = volume(self.front);assert updated + 1e-11 >= self.hv
                self.hv = updated;self.admissions += 1
            self.fe = fe
            if fe in self.checks:self.checkpoint(fe)
        return self.hv

    def checkpoint(self, fe):
        expected = (np.asarray(self.checks[fe]['front']) - self.lower) / self.scale
        assert set(map(tuple, expected)) == set(map(tuple, self.front)), 'Full paid replay checkpoint front differs'
        error = abs(self.hv - hypervolume(self.front, (1.5,) * 3));assert error < 1e-11
        self.max_hv_error = max(self.max_hv_error, error);self.checked.add(fe)

    def endpoint_gain(self, entry_front, entry_hv, objective):
        normalized = (np.asarray(objective) - self.lower) / self.scale
        return max(0., volume(np.vstack([entry_front, normalized])) - entry_hv)

    def finish(self, limit):
        self.advance(limit)
        assert next(self.records, None) is None and self.checked == self.checks.keys()
        self.stream.close()
        return {'paidRows': self.fe, 'intraRows': self.inside, 'phaseRows': self.phases,
                'archiveAdmissionsIndependentlyVerified': self.admissions,
                'checkedFEFronts': sorted(self.checked), 'maxIndependentHVError': self.max_hv_error}
