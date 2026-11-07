"""Freeze a metadata-only sampling correction before any probe outcome exists."""
import argparse
from pathlib import Path
from common import linux, read, write


def amend(root):
    linux()
    assert not list(root.glob('engineering/**/receipt.json'))
    assert not list(root.glob('science/**/receipt.json'))
    audit=read(root/'request-audit.json')
    assert all([r['cycle'] for r in c['sampled']]==[5,6,7,8] for c in audit['contexts'])
    value=dict(version='REQUEST_PRODUCTION_AMENDMENT-01',probeFEAtAmendment=0,
        reason='Every source starts mature phase at the same request cycle; first-four policy unintentionally excludes all tight0.9 requests',
        evidence='request-audit.json preserves all 600 real requests and the 24 original selected contexts; inputs/ preserved',
        selectionBasis='Actual cycle metadata only, not feasibility, gains, fronts, or candidate outcomes',
        requestCycles=[0,4,8],selection='First occurrence of each cycle in original selected family; no replacement if absent',
        inputDirectory='inputs-v2',requestsPerSource=3,scienceRuns=72,scienceFE=36864,
        effectiveShuffle='Cyclic next among these three historical requests, all known at common POST_GLOBAL barrier',
        sourceNewFEChange=0,instancesChanged=False,seedsChanged=False,
        unchanged='Original cap values, eta values, algorithm, acceptance, selector, FE512 perarm, metrics and thresholds',
        aggregation='Median request-paired effects within each source seed, then median/range/signs across three seeds',
        costReduction=12288,limitation='Three sampled request regimes per source; not complete nine-grid or general online evidence')
    write(root/'amendment-01.json',value)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    amend(p.parse_args().root)
