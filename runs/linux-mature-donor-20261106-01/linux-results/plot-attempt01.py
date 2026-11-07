"""All preregistered paired effects, final archive and working state; Linux only."""
import argparse
import json
from pathlib import Path
import platform
import time
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


CONTRACT = {
    'claim': 'Display the observed metric disagreement without promoting a donor pool from HV alone.',
    'archetype': 'quantitative grid', 'backend': 'Python matplotlib',
    'panels': 'Final all-paid archive and final working-population paired HV,IGDplus,Cdifference',
    'mapping': 'Every registered comparison and every paired source seed; black vertical markers show medians',
    'unit': 'Three reused developmental mature snapshots per instance, not independent algorithm qualification',
    'statistics': 'Raw paired values and descriptive medians; no test, confidence interval or EAF',
    'reuse': 'Style-only inheritance of previously accepted pilot typography; new effect plot semantics',
    'exclusions': 'None within the declared paired-effect panel scope; raw fronts/extremes remain in analysis.json',
    'formats': ['SVG editable text', 'PDF TrueType', 'PNG 600dpi'], 'widthMM': 183, 'heightMM': 118,
}


def values(pair):
    return [pair['HVEffectPct']['1.5'], pair['IGDplusSymmetricImprovementPct'], 100 * pair['Cdelta']]


def plot(analysis, out):
    started = time.perf_counter()
    with analysis.open() as stream: result = json.load(stream)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'figure-contract.json').write_text(json.dumps(CONTRACT, indent=2))
    plt.rcParams.update({'font.family': 'sans-serif', 'font.sans-serif': ['DejaVu Sans'], 'font.size': 7,
                         'axes.titlesize': 8, 'axes.labelsize': 7, 'legend.fontsize': 6.5,
                         'svg.fonttype': 'none', 'pdf.fonttype': 42,
                         'axes.spines.right': False, 'axes.spines.top': False, 'axes.linewidth': 0.7,
                         'legend.frameon': False})
    all_values = np.asarray([values(p) for case in result['instances'] for c in case['comparisons'] for p in c['pairs']])
    maxima = np.maximum(np.abs(all_values).max(axis=0), 1e-5) * 1.15
    colors, markers = ['#4477AA', '#CC9955', '#55A899'], ['o', 's', '^']
    titles = ['HV relative change (%)', 'IGD+ symmetric\nimprovement (%)', 'C(A,B) - C(B,A)\n(percentage points)']
    exports = []
    for case in result['instances']:
        fig, axes = plt.subplots(2, 3, figsize=(183 / 25.4, 118 / 25.4))
        fig.subplots_adjust(left=0.16, right=0.98, top=0.82, bottom=0.18, wspace=0.32, hspace=0.65)
        for row, endpoint in enumerate(['finalArchive', 'workingPopulation']):
            records = [c for c in case['comparisons'] if c['endpoint'] == endpoint]
            labels = [c['candidate'] + ' / ' + c['control'] for c in records]
            for column in range(3):
                axis = axes[row, column]
                axis.axvline(0, color='#777777', linewidth=0.6)
                for i, comp in enumerate(records):
                    points = np.asarray([values(p) for p in comp['pairs']])[:, column]
                    for j, value in enumerate(points):
                        axis.plot(value, i + (j-1) * 0.15, marker=markers[j], color=colors[j], markersize=3.5, linestyle='none',
                                  label=str(comp['pairs'][j]['seed']) if row == column == i == 0 else None)
                    axis.plot(float(np.median(points)), i, marker='|', color='black', markersize=9, linestyle='none')
                axis.set(xlim=(-maxima[column], maxima[column]), ylim=(len(records)-0.5, -0.5), yticks=range(len(records)))
                axis.set_yticklabels(labels if column == 0 else [''] * len(labels))
                axis.set_title(titles[column], pad=13)
                axis.locator_params(axis='x', nbins=4)
                axis.grid(axis='x', alpha=0.15, linewidth=0.5)
                axis.text(-0.08, 1.22, chr(ord('a') + row*3+column), transform=axis.transAxes, fontsize=8, fontweight='bold')
            axes[row, 0].set_ylabel('All-paid archive' if row == 0 else 'Working population', labelpad=5)
        fig.suptitle(case['instance'] + ' | one mature receiver pass | all paired effects', y=0.985, fontsize=9)
        handles, labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.55, 0.95), ncol=3)
        fig.text(0.5, 0.065, 'Positive values favour A. Points: all three paired source seeds; black marks: medians. No confidence intervals.', ha='center', fontsize=6)
        fig.text(0.5, 0.025, 'R: original live donors; G/S: add paid global/shared donors; UNION: ordinary combined pool. Not a full-algorithm trial.', ha='center', fontsize=6)
        stem = out / ('paired-effects-' + case['instance'])
        fig.savefig(str(stem) + '.svg')
        fig.savefig(str(stem) + '.pdf')
        fig.savefig(str(stem) + '.png', dpi=600)
        fig.savefig(str(stem) + '-preview.png', dpi=150)
        texts = ET.parse(str(stem) + '.svg').findall('.//{http://www.w3.org/2000/svg}text')
        exports.append({'stem': stem.name, 'svgTextElements': len(texts), 'widthMM': 183, 'heightMM': 118, 'source': str(analysis),
                        'pairedComparisons': 10, 'rawEffectPoints': 90, 'visualInspection': 'PENDING'})
        assert len(texts) > 0
        plt.close(fig)
    (out / 'figure-export.json').write_text(json.dumps({'exports': exports, 'seconds': time.perf_counter()-started}, indent=2))
    print('PLOT_COMPLETE', out, flush=True)


if __name__ == '__main__':
    assert platform.system() == 'Linux'
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plot(args.analysis, args.output)
