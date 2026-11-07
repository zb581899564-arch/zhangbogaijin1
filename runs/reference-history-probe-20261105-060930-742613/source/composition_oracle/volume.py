"""Disjoint uncovered boxes for fast single-point HV additions against one fixed archive."""
import numpy as np


class UncoveredVolume:
    def __init__(self, background, reference):
        self.reference = np.asarray(reference, dtype=float)
        background = np.asarray(background, dtype=float).reshape(-1, 3)
        assert np.all(background >= 0) and np.all(self.reference > 0)
        points = background[np.all(background < self.reference, axis=1)]
        xs = sorted({0., self.reference[0], *points[:, 0].tolist()})
        boxes = []
        for left, right in zip(xs[:-1], xs[1:]):
            active = sorted(map(tuple, points[points[:, 0] <= left, 1:]))
            last, bottom = 0., self.reference[2]
            for energy, wage in active:
                if wage >= bottom:
                    continue
                if energy > last:
                    boxes.append((left, right, last, energy, bottom))
                last, bottom = energy, wage
            if last < self.reference[1] and bottom > 0:
                boxes.append((left, right, last, self.reference[1], bottom))
        self.boxes = np.asarray(boxes, dtype=float).reshape(-1, 5)
        widths = (self.boxes[:, 1]-self.boxes[:, 0]) * (self.boxes[:, 3]-self.boxes[:, 2]) * self.boxes[:, 4]
        self.background_hv = float(np.prod(self.reference) - np.sum(widths))

    def gains(self, points):
        points = np.asarray(points, dtype=float).reshape(-1, 3)
        assert np.all(points >= 0)
        result = []
        for begin in range(0, len(points), 64):
            chunk = points[begin:begin+64]
            x = np.maximum(0., self.boxes[None, :, 1] - np.maximum(self.boxes[None, :, 0], chunk[:, None, 0]))
            y = np.maximum(0., self.boxes[None, :, 3] - np.maximum(self.boxes[None, :, 2], chunk[:, None, 1]))
            z = np.maximum(0., self.boxes[None, :, 4] - chunk[:, None, 2])
            result.extend(np.sum(x*y*z, axis=1).tolist())
        return np.asarray(result)


def engineering_checks(hypervolume):
    background = np.asarray([[.2, .7, .5], [.5, .2, .4], [.3, .4, .8], [.2, .7, .5]])
    points = np.asarray([[.1, .1, .1], [.9, .9, .9], [0., 0., 0.], [1.2, .3, .3],
                         [.2, .7, .5], [.2, .5, .3], [.15, .8, .2]])
    errors = []
    for reference in ((1.,)*3, (1.25,)*3, (2.,)*3):
        scorer = UncoveredVolume(background, reference)
        baseline = hypervolume(background, reference)
        assert abs(scorer.background_hv-baseline) < 1e-12
        expected = [hypervolume(np.vstack([background, p]), reference)-baseline for p in points]
        error = float(np.max(np.abs(scorer.gains(points)-expected)))
        assert error < 1e-12
        errors.append({'reference': reference, 'points': len(points), 'maxError': error, 'status': 'PASS'})
    empty = UncoveredVolume([], (1.,)*3)
    assert np.allclose(empty.gains([[.5, .5, .5]]), [.125], atol=1e-15, rtol=0)
    return errors
