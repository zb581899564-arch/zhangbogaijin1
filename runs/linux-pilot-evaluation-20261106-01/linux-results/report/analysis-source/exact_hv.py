"""Exact compiled 3D HV for offline event accounting; no search dependency."""
import numpy as np
import moocore


def exact_hv(points, reference):
    points=np.asarray(points,dtype=float).reshape(-1,3)
    reference=np.asarray(reference,dtype=float)
    if reference.shape!=(3,) or not np.isfinite(points).all() or not np.isfinite(reference).all():
        raise ValueError('Finite three-objective input required')
    if not len(points):
        return 0.0
    return float(moocore.hypervolume(points,ref=reference,maximise=False))
