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
