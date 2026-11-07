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
