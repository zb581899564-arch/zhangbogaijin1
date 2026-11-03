"""Materialize the exact fatigue and setup values; seeds are not a cross-language contract."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.fatigue_mechanism.instances import load_instance, fatigue_profile

PROFILES = {
    "weak": dict(alpha_per_base=.10, mu_per_base=.8, beta=.1),
    "strong_slow": dict(alpha_per_base=.45, mu_per_base=.08, beta=.7),
    "strong_fast": dict(alpha_per_base=.45, mu_per_base=.8, beta=.7),
    "beta0": dict(alpha_per_base=.45, mu_per_base=.8, beta=0.),
}


def materialize(instance_path: Path, output: Path, setup_seed: int, profile: str, parameter_seed: int):
    instance = load_instance(instance_path, setup_seed)
    params, metadata = fatigue_profile(instance, PROFILES[profile], parameter_seed)
    setup_path = output / "RECONSTRUCTED-setup.txt"
    fatigue_path = output / "fatigue-input.txt"
    setup_path.write_text("# source=" + instance.setup_source + "\n" +
                          "\n".join(",".join(map(str, row)) for row in instance.setup) + "\n", encoding="utf-8")
    arrays = params.arrays(instance)
    rows = []
    for f in range(instance.factories):
        for k in range(instance.stages):
            for w in range(len(instance.efficiencies[f][k])):
                uid = instance.worker_uid(f, k, w)
                rows.append(",".join(map(str, [f, k, w, *(float(a[uid]) for a in arrays)])))
    fatigue_path.write_text("# source=SYNTHETIC; time-scaled worker heterogeneity; profile=" + profile
                            + "; seed=" + str(parameter_seed) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return instance, params, metadata
