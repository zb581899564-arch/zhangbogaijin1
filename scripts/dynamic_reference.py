"""Prepare independently evaluated Python schedules for Java numerical cross-checks."""
from pathlib import Path
import numpy as np
from dynamic_inputs import materialize
from research.fatigue_mechanism.instances import parent_genome
from research.fatigue_mechanism.decoder import decode


def reference_cases(root: Path, data: Path):
    root.mkdir()
    manifest, cases = [], 0
    for index, source in enumerate(sorted(data.glob("*.txt"))):
        folder = root / source.stem
        try:
            # Validate qualification before creating the instance's evidence folder.
            from research.fatigue_mechanism.instances import load_instance
            load_instance(source, 314159 + index)
        except ValueError as error:
            if "Eq8" in str(error):
                continue
            raise
        folder.mkdir()
        instance, params, _ = materialize(source, folder, 314159 + index, "strong_fast", 271828 + index)
        rows = []
        for seed in (202611101, 202611103, 202611107):
            genome = parent_genome(instance, seed)
            result = decode(instance, genome, params)
            arrays = [genome.js, genome.fa, genome.ma, genome.wa, result.objectives, result.C, result.v,
                      [o.machine_id for o in result.operations], [o.worker_id for o in result.operations]]
            rows.append("\t".join(",".join(map(str, a)) for a in arrays))
            cases += 1
        (folder / "reference.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        manifest.append(source.name + "\t" + source.stem)
    (root / "manifest.tsv").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    if len(manifest) != 36 or cases != 108:
        raise AssertionError(f"Unexpected qualification: {len(manifest)} instances / {cases} cases")
    return cases
