"""Reproducible quantitative grids for a fixed three-seed phase-budget diagnosis."""
import numpy as np

from figure_exports import COLORS, CONTRACT, MARKERS, MM, panel_label, save_figure, setup
from front_plotting import front_figures
from report_io import require_linux, write_json


def _convergence(plt, rows, plan, out):
    exports = []
    names = (("HV", "Hypervolume (larger is better)"), ("IGDplus", "IGD+ (smaller is better)"),
             ("IGD", "IGD (smaller is better)"))
    checkpoints = plan["checkpoints"]
    for spec in plan["instances"]:
        instance = spec["stem"]
        fig, axes = plt.subplots(1, 3, figsize=(183 * MM, 74 * MM))
        fig.subplots_adjust(left=0.08, right=0.98, bottom=0.23, top=0.75, wspace=0.4)
        for letter, axis, (metric, title) in zip("abc", axes, names):
            for arm in plan["arms"]:
                values = []
                for seed in plan["seeds"]:
                    lookup = {row["checkpoint"]: row for row in rows if row["instance"] == instance and row["arm"] == arm and row["seed"] == seed}
                    series = [lookup[checkpoint][metric] for checkpoint in checkpoints]
                    if any(value is None for value in series):
                        raise ValueError("Registered convergence panel contains a missing metric")
                    values.append(series)
                    axis.plot(checkpoints, series, color=COLORS[arm], alpha=0.28, linewidth=0.65)
                array = np.asarray(values)
                axis.fill_between(checkpoints, array.min(axis=0), array.max(axis=0), color=COLORS[arm], alpha=0.1, linewidth=0)
                axis.plot(checkpoints, np.median(array, axis=0), color=COLORS[arm], marker=MARKERS[arm],
                          markersize=3, linewidth=1.5, label=arm)
            axis.set(title=title, xlabel="Successful FE", xlim=(0, plan["fePerRun"]))
            axis.set_xticks([0, 250000, 500000], labels=["0", "250k", "500k"])
            axis.grid(alpha=0.18, linewidth=0.5)
            axis.locator_params(axis="y", nbins=4)
            panel_label(axis, letter)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.54, 0.94), ncol=3)
        fig.suptitle(f"{instance} | common-reference convergence", y=0.995, fontsize=9)
        fig.text(0.5, 0.045, "n = 3 paired seeds. Thin lines: all seeds; thick line: median; band: min-max, not a confidence interval.",
                 ha="center", fontsize=6.5)
        exports.append(save_figure(fig, out, f"convergence-{instance}", source_data=["convergence.csv", "reference-fronts.json"],
                                   description="All registered FE checkpoints; the diagnostic FE 1/2 records remain in source CSV but are outside this planned panel scope."))
    return exports


def _budgets(plt, rows, plan, out):
    exports = []
    phases = ("INITIAL", "GLOBAL", "LOCAL", "LIFECYCLE")
    phase_colors = ("#BBBBBB", "#4477AA", "#CC9955", "#667788")
    for spec in plan["instances"]:
        instance = spec["stem"]
        keys = [(arm, seed) for arm in plan["arms"] for seed in plan["seeds"]]
        lookup = {(row["arm"], row["seed"], row["phase"]): row for row in rows if row["instance"] == instance}
        fig, axes = plt.subplots(2, 1, figsize=(183 * MM, 108 * MM), sharex=True)
        fig.subplots_adjust(left=0.13, right=0.98, bottom=0.19, top=0.84, hspace=0.28)
        x = np.arange(len(keys))
        for letter, axis, metric, ylabel in zip("ab", axes, ("successfulFE", "secondsInclusive"),
                                               ("Successful FE", "Inclusive phase seconds")):
            bottom = np.zeros(len(keys))
            for phase, color in zip(phases, phase_colors):
                values = np.asarray([lookup[(arm, seed, phase)][metric] for arm, seed in keys])
                axis.bar(x, values, bottom=bottom, width=0.72, color=color, edgecolor="white", linewidth=0.3, label=phase)
                bottom += values
            axis.set_ylabel(ylabel)
            axis.grid(axis="y", alpha=0.15, linewidth=0.5)
            axis.set_axisbelow(True)
            axis.locator_params(axis="y", nbins=4)
            for boundary in (2.5, 5.5):
                axis.axvline(boundary, color="#BBBBBB", linewidth=0.5)
            panel_label(axis, letter)
        labels = [f"{ {'FULL': 'F', 'GLOBAL_ONLY': 'G', 'LOCAL_ONLY': 'L'}[arm]}{plan['seeds'].index(seed) + 1}" for arm, seed in keys]
        axes[-1].set_xticks(x, labels=labels)
        axes[-1].set_xlabel("F = FULL; G = GLOBAL_ONLY; L = LOCAL_ONLY")
        handles, legend = axes[0].get_legend_handles_labels()
        fig.legend(handles, legend, loc="upper center", bbox_to_anchor=(0.55, 0.94), ncol=4)
        fig.suptitle(f"{instance} | actual phase budgets and inclusive cost", y=0.995, fontsize=9)
        fig.text(0.5, 0.03, "Seed suffixes: " + "; ".join(f"{i + 1} = {seed}" for i, seed in enumerate(plan["seeds"])), ha="center", fontsize=6.5)
        exports.append(save_figure(fig, out, f"budgets-{instance}", source_data=["stage-costs.csv"],
                                   description="All nine runs, exact stacked phase FE and inclusive phase seconds. Sharing remains nested in GLOBAL; no causal share is implied."))
    return exports


def render_figures(final_rows, convergence, stages, plan, out):
    require_linux()
    out.mkdir(exist_ok=False)
    plt = setup()
    write_json(out / "figure-contract.json", CONTRACT)
    exports = _convergence(plt, convergence, plan, out)
    exports.extend(front_figures(plt, final_rows, plan, out))
    exports.extend(_budgets(plt, stages, plan, out))
    write_json(out / "figure-qa.json", {"exports": exports, "backend": "Python matplotlib",
                                       "visualReviewComplete": False, "sameTimeQualityClaim": False})
    captions = ["# 图说明", "", "所有曲线和散点来自本报告的原始表；不删 seed、不按结果改尺度。", ""]
    for row in exports:
        captions.extend([f"- `{row['stem']}`：{row['description']} 来源：{', '.join(row['sourceData'])}"])
    (out / "CAPTIONS.md").write_text("\n".join(captions) + "\n", encoding="utf-8")
    return exports
