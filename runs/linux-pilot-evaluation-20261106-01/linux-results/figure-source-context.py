"""Python publication exports and traceable figure contract; visual QA remains explicit."""
from pathlib import Path
import xml.etree.ElementTree as ET

from report_io import require_linux


COLORS = {"FULL": "#4477AA", "GLOBAL_ONLY": "#CC9955", "LOCAL_ONLY": "#55A899"}
MARKERS = {"FULL": "o", "GLOBAL_ONLY": "s", "LOCAL_ONLY": "^"}
MM = 1 / 25.4
CONTRACT = {
    "coreClaim": "Display measured tradeoffs from assigning the same FE budget to three phase schedules; do not presuppose superiority.",
    "archetype": "quantitative grid", "backend": "Python matplotlib only",
    "panels": {"convergence": "Registered FE checkpoints, all paired seeds, median and min-max range",
               "fronts": "Every final front and every seed, 3D and all three 2D projections with shared per-instance limits",
               "budgets": "Actual per-seed phase FE and inclusive seconds, with INITIAL separate"},
    "widthMM": 183, "formats": ["editable-text SVG", "PDF fonttype 42", "PNG 600 dpi"],
    "n": "Three independent search seeds within each of two reused development instances",
    "statistics": "Descriptive; no confidence interval, significance test or multiplicity-adjusted claim",
    "risk": "Two-dimensional projections cannot establish three-objective dominance; phase gains are not causal percentages",
    "eaf": "No 50% EAF or EAF-difference display below five paired seeds",
}


def setup():
    require_linux()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
                               "font.size": 7, "axes.labelsize": 8, "axes.titlesize": 8,
                               "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
                               "svg.fonttype": "none", "pdf.fonttype": 42,
                               "axes.spines.right": False, "axes.spines.top": False,
                               "axes.linewidth": 0.7, "legend.frameon": False, "figure.facecolor": "white"})
    return plt


def save_figure(figure, out, stem, *, source_data, description):
    require_linux()
    import matplotlib.pyplot as plt
    figure.canvas.draw()
    files = []
    paths = (Path(out) / f"{stem}.svg", Path(out) / f"{stem}.pdf", Path(out) / f"{stem}.png")
    for path in paths:
        if path.exists():
            raise FileExistsError(path)
        figure.savefig(path, dpi=600 if path.suffix == ".png" else None, facecolor="white")
        if path.stat().st_size == 0:
            raise ValueError("Empty figure export")
        files.append(path.name)
    root = ET.parse(Path(out) / f"{stem}.svg").getroot()
    texts = root.findall(".//{http://www.w3.org/2000/svg}text")
    if not texts:
        raise ValueError("SVG lost editable text")
    preview = plt.imread(Path(out) / f"{stem}.png")
    item = {"stem": stem, "files": files, "sourceData": source_data, "description": description,
            "svgEditableTextElements": len(texts), "pngPixels": [preview.shape[1], preview.shape[0]],
            "physicalSizeMM": (figure.get_size_inches() * 25.4).tolist(),
            "pdfFonttypeConfigured": 42, "dataExclusion": "None within the declared panel scope",
            "visualInspection": "PENDING_PARENT_REVIEW", "sourcePreflight": "PENDING_SKILL_VALIDATOR"}
    plt.close(figure)
    return item


def panel_label(axis, text):
    axis.text(-0.14, 1.04, text, transform=axis.transAxes, fontweight="bold", fontsize=8, va="bottom")


"""All final points, fixed shared axes, and explicit three-objective limitations."""
import numpy as np

from figure_exports import COLORS, MARKERS, MM, panel_label, save_figure


NAMES = ("Cmax / scale", "TEC / scale", "TWC / scale")


def _limits(rows):
    all_points = np.vstack([row["normalizedFront"] for row in rows])
    lower, upper = all_points.min(axis=0), all_points.max(axis=0)
    padding = np.maximum(upper - lower, np.maximum(np.abs(upper), 1) * 0.01) * 0.07
    return [(float(a - p), float(b + p)) for a, b, p in zip(lower, upper, padding)]


def front_figures(plt, final_rows, plan, out):
    exports = []
    for spec in plan["instances"]:
        instance = spec["stem"]
        selected = [row for row in final_rows if row["instance"] == instance]
        limits = _limits(selected)
        for seed in plan["seeds"]:
            rows = [row for row in selected if row["seed"] == seed]
            fig = plt.figure(figsize=(183 * MM, 142 * MM))
            grid = fig.add_gridspec(2, 2, left=0.11, right=0.97, bottom=0.12, top=0.86, wspace=0.38, hspace=0.47)
            three = fig.add_subplot(grid[0, 0], projection="3d")
            axes = [fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, 0]), fig.add_subplot(grid[1, 1])]
            for row in rows:
                data = np.asarray(row["normalizedFront"])
                options = {"color": COLORS[row["arm"]], "marker": MARKERS[row["arm"]],
                           "s": 10, "alpha": 0.7, "edgecolors": "none", "label": row["arm"]}
                three.scatter(data[:, 0], data[:, 1], data[:, 2], depthshade=False, **options)
                for axis, (a, b) in zip(axes, ((0, 1), (0, 2), (1, 2))):
                    axis.scatter(data[:, a], data[:, b], **options)
            three.set(xlim=limits[0], ylim=limits[1], zlim=limits[2])
            three.set_xlabel(NAMES[0], labelpad=1)
            three.set_ylabel(NAMES[1], labelpad=1)
            three.set_zlabel(NAMES[2], labelpad=1)
            three.tick_params(pad=0, labelsize=6)
            three.view_init(elev=22, azim=225)
            three.set_box_aspect((1, 1, 0.8))
            three.text2D(-0.08, 1.04, "a", transform=three.transAxes, fontweight="bold", fontsize=8)
            for letter, axis, (a, b) in zip("bcd", axes, ((0, 1), (0, 2), (1, 2))):
                axis.set(xlabel=NAMES[a], ylabel=NAMES[b], xlim=limits[a], ylim=limits[b])
                axis.grid(alpha=0.15, linewidth=0.5)
                axis.ticklabel_format(style="plain", useOffset=False)
                axis.locator_params(nbins=4)
                panel_label(axis, letter)
            handles, labels = axes[0].get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.53, 0.965), ncol=3, markerscale=1.4)
            fig.suptitle(f"{instance} | seed {seed} | final fronts at {plan['fePerRun']:,} FE", y=0.995, fontsize=9)
            fig.text(0.5, 0.02, "All objectives minimized. All points shown; axes shared across seeds. 2D projections do not establish 3D dominance.",
                     ha="center", fontsize=6.5)
            exports.append(save_figure(fig, out, f"fronts-{instance}-{seed}", source_data=["fronts.csv", "final-metrics.json"],
                                       description="One paired seed, all three full final fronts; three projections use the same per-instance objective limits."))
    return exports


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
