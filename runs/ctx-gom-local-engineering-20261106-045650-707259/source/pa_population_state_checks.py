"""Numeric state identities, genotype decoding and old-archive exact notifications."""
import hashlib
import struct

import numpy as np


def identity(point):
    n = len(point['resources'])
    payload = struct.pack('>i', n) + struct.pack('>' + 'i'*n, *point['resources'])
    payload += struct.pack('>' + 'd'*n, *point['keys']) + struct.pack('>ddd', *point['objectives'])
    return hashlib.sha256(payload).hexdigest()


def vectors(point, catalog):
    order = sorted(range(len(point['resources'])), key=lambda j: (point['keys'][j], -j))
    return [order, *[[catalog[point['resources'][j]][k] for j in order] for k in range(3)]]


def physical(point, catalog):
    js, fa, ma, wa = vectors(point, catalog)
    return tuple(tuple((j, m, w) for j, f, m, w in zip(js, fa, ma, wa) if f == factory)
                 for factory in range(max(t[0] for t in catalog) + 1))


def paid_bytes(point, catalog, fe):
    result = struct.pack('>q', fe)
    for vector in vectors(point, catalog):
        result += struct.pack('>i', len(vector)) + struct.pack('>' + 'i'*len(vector), *vector)
    return result + struct.pack('>ddd', *point['objectives'])


def snapshot(event, actual):
    for key in ('id', 'paidFE', 'role', 'hash', 'objectives'):
        assert event[key] == actual[key], ('State snapshot mismatch', key, event['id'])


def offer(archive, event):
    obj = np.array(event['objectives']); assert obj.shape == (3,) and np.isfinite(obj).all()
    if len(archive):
        dominated = bool(np.any(np.all(archive <= obj, axis=1) & np.any(archive < obj, axis=1)))
        equal = bool(np.any(np.all(archive == obj, axis=1)))
    else:
        dominated = equal = False
    assert event['archiveDominated'] == dominated and event['archiveEqual'] == equal
    assert event['archiveFresh'] == (not dominated and not equal) and event['archiveSizeBefore'] == len(archive)
    if not dominated and not equal:
        remove = np.all(obj <= archive, axis=1) & np.any(obj < archive, axis=1)
        archive = np.vstack([archive[~remove], obj])
    assert event['archiveSizeAfter'] == len(archive)
    return archive
