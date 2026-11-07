"""Disjoint source accounting; fixed families and free80 are never conflated."""
from collections import Counter, defaultdict
from analysis_common import json_lines, read_json


def counts():
    return dict(proposals=0, accepted=0, admitted=0, equal=0, dominated=0, fallback=0)


def supply_summary(folder, capture):
    source = defaultdict(counts)
    family = defaultdict(counts)
    source_family = defaultdict(counts)
    for step in json_lines(folder / "steps.jsonl"):
        source_name = step["donorType"]
        group = "free80" if step["family"] < 0 else "fixed20"
        for target in (source[source_name], family[group], source_family[f"{group}/{source_name}"]):
            target["proposals"] += 1
            for name in ("accepted", "admitted", "equal", "dominated", "fallback"):
                target[name] += int(step[name])
    views = read_json(folder / "views.json")
    unique = Counter(("free80" if v["family"] < 0 else "fixed20", v["source"]) for v in views)
    raw = Counter()
    with (capture / "points.tsv").open(encoding="utf-8-sig") as stream:
        for line in stream:
            fields = line.rstrip("\n").split("\t")
            raw[("free80" if int(fields[4]) < 0 else "fixed20", fields[0])] += 1
    for name in ("R", "G", "S", "GS"):
        source[name]
        for group in ("free80", "fixed20"):
            source_family[f"{group}/{name}"]
    return dict(byDisjointDonorSource=dict(source), byReceiverDomain=dict(family),
                byReceiverDomainAndSource=dict(source_family),
                rawCaptureCounts={f"{g}/{s}": n for (g, s), n in sorted(raw.items())},
                uniqueExternalCounts={f"{g}/{s}": n for (g, s), n in sorted(unique.items())},
                free80SharedRaw=raw["free80", "S"],
                free80SharedAvailable=unique["free80", "S"] + unique["free80", "GS"],
                overlapAccounting="GS is a separate disjoint category, counted once; never added to both G and S",
                zeroSharedInterpretation="No S/free80 draw with no eligible S/free80 supply is an unavailable treatment, not evidence of no effect")
