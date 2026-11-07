"""Verify extracted P100/C100 against the immutable already-paid source window."""
from collections import Counter
import hashlib
from pathlib import Path

from audit_core import (ROLE_COUNTS, check_population, check_raw, factory_by_job,
                        points_tsv, read_json, require, same_front)
from audit_selection import member_identity


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_input(directory, catalog):
    metadata = read_json(directory / "selection-source.json")
    require(metadata["passed"] and metadata["newSourceFE"] == metadata["newDecoderCalls"] == 0,
            "Input source was not a successful zero-cost extraction")
    require(digest(directory / "points.tsv") == metadata["extractedSHA256"] and
            digest(directory / "background.tsv") == metadata["backgroundSHA256"],
            "Extracted input artifact hash changed")
    rows = points_tsv(directory / "points.tsv")
    require(len(rows) == 200, "Input must be P100 plus C100")
    parents, children = rows[:100], rows[100:]
    check_population(parents)
    check_population(children)
    for origin, cohort in (("P", parents), ("C", children)):
        require([p["sourceIndex"] for p in cohort] == list(range(100)) and
                all(p["origin"] == origin for p in cohort), "Input source slot sequence differs")
    for parent, child in zip(parents, children):
        require((parent["role"], parent["family"]) == (child["role"], child["family"]),
                "P/C pair role or family differs")
        if parent["family"] >= 0:
            require(factory_by_job(parent["raw"]) == factory_by_job(child["raw"]),
                    "P/C fixed family allocation differs")
    for row in rows:
        require(0 <= row["sourcePaidByFE"] <= metadata["afterGlobalFE"], "Imported source is from the future")
        check_raw(row["raw"], catalog["jobs"], catalog["factories"])
    background = [[float(value) for value in line.split("\t")]
                  for line in (directory / "background.tsv").read_text().splitlines() if line.strip()]
    verify_source(directory, metadata, parents, children, background)
    return dict(parents=parents, children=children, A0=background, metadata=metadata)


def verify_source(directory, metadata, parents, children, background):
    source = Path(metadata["sourceCapture"])
    require(digest(source / "points.tsv") == metadata["sourceSHA256"], "Historical capture hash changed")
    original = points_tsv(source / "points.tsv")
    require(len(original) == 5100, "Historical capture is not P100 plus paid global5000")
    require([member_identity(p) for p in parents] == [member_identity(p) for p in original[:100]],
            "Extracted parents differ from historical capture")
    require(len(metadata["pairs"]) == 100, "Missing P/C correspondence records")
    candidates = original[100:]
    require([p["sourceIndex"] for p in candidates] == list(range(5000)), "Historical child ordinal changed")
    require([p["sourcePaidByFE"] for p in candidates] ==
            list(range(metadata["beforeGlobalFE"] + 1, metadata["afterGlobalFE"] + 1)),
            "Historical child fee sequence is incomplete")
    first = {role: [p for p in candidates if p["role"] == role][:count]
             for role, count in ROLE_COUNTS.items()}
    used = Counter()
    for index, (parent, child, pair) in enumerate(zip(parents, children, metadata["pairs"])):
        role = parent["role"]
        source_child = first[role][used[role]]
        used[role] += 1
        expected = dict(source_child, origin="C", sourceIndex=index)
        require(member_identity(child) == member_identity(expected), "Extracted C is not the actual role first batch")
        require(pair == dict(parentIndex=index, childIndex=source_child["sourceIndex"],
                             childPaidByFE=source_child["sourcePaidByFE"], role=role,
                             family=source_child["family"], source=source_child["origin"], batch=0),
                "Source correspondence record differs")
    same_front(background, read_json(source / "background.json"), "Historical POST_GLOBAL A0")
    same_front(background, read_json(directory / "background.json"), "Extracted A0")
